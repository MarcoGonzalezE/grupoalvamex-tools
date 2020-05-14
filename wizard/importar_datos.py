# -*- coding: utf-8 -*-
# Importacion de datos

from odoo import api, fields, models, _
from datetime import datetime
from odoo.exceptions import UserError, AccessError
import csv
import base64
import io as StringIO
import xlrd
from odoo.tools import ustr

class purchase_order(models.Model):
    _inherit = "purchase.order"
    
    @api.multi
    def importar_compras(self):
        if self:
            action = self.env.ref('grupoalvamex_tools.sh_import_pol_action').read()[0]
            return action

class ImportarLineasComprasWizard(models.TransientModel):
    _name="import.pol.wizard"

    import_type = fields.Selection([
        ('csv','CSV'),
        ('excel','Excel')
        ],default="csv",string="Tipo de Importacion",required=True)
    file = fields.Binary(string="Archivo",required=True)   
    product_by = fields.Selection([
        ('name','Nombre'),
        ('int_ref','Referencia Interna'),
        ('barcode','Codigo de Barras')
        ],default="name", string = "Buscar producto por", required = True) 

    @api.multi
    def show_success_msg(self,counter,skipped_line_no):
        
        #to close the current active wizard        
        action = self.env.ref('grupoalvamex_tools.sh_import_pol_action').read()[0]
        action = {'type': 'ir.actions.act_window_close'} 
        
        #open the new success message box    
        view = self.env.ref('grupoalvamex_tools.sh_message_wizard')
        view_id = view and view.id or False                                   
        context = dict(self._context or {})
        dic_msg = str(counter) + " Registros importados exitosamente"
        if skipped_line_no:
            dic_msg = dic_msg + "\nNota:"
        for k,v in skipped_line_no.items():
            dic_msg = dic_msg + "\nFila N. " + k + " " + v + " "
        context['message'] = dic_msg            
        
        return {
            'name': 'Informacion',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sh.message.wizard',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': context,
            }   

    
    @api.multi
    def import_pol_apply(self):
        pol_obj = self.env['purchase.order.line']
        #perform import lead
        if self and self.file and self.env.context.get('sh_po_id',False):
            #For CSV
            if self.import_type == 'csv':
                counter = 1
                skipped_line_no = {}
                try:
                    file = str(base64.decodestring(self.file).decode('utf-8'))
                    myreader = csv.reader(file.splitlines())
                    skip_header=True
                     
                    for row in myreader:
                        try:
                            if skip_header:
                                skip_header=False
                                counter = counter + 1
                                continue

                            if row[0] != '': 
                                vals={}
                                
                                field_nm = 'name'
                                if self.product_by == 'name':
                                    field_nm = 'name'
                                elif self.product_by == 'int_ref':
                                    field_nm = 'default_code'
                                elif self.product_by == 'barcode':
                                    field_nm = 'barcode'
                                
                                search_product = self.env['product.product'].search([(field_nm,'=',row[0])], limit = 1)
                                if search_product:
                                    vals.update({'product_id' : search_product.id})
                                    
                                    if row[1] != '':
                                        vals.update({'name' : row[1] })
                                    else:
                                        vals.update({'name' : search_product.name})
                                        
                                        active_po = self.env['purchase.order'].search([('id','=',self.env.context.get('sh_po_id'))])
                                        if active_po:
                                            product_lang = search_product.with_context({
                                                'lang': active_po.partner_id.lang,
                                                'partner_id': active_po.partner_id.id,
                                            })
                                            pro_desc = product_lang.display_name
                                            if product_lang.description_purchase:
                                                pro_desc += '\n' + product_lang.description_purchase 
                                            vals.update({'name' : pro_desc})                                       

                                    if row[2] != '':
                                        vals.update({'product_qty' : row[2] })
                                    else:
                                        vals.update({'product_qty' : 1 })
                                    
                                    if row[3] in (None,"") and search_product.uom_po_id:
                                        vals.update({'product_uom' : search_product.uom_po_id.id })
                                    else:
                                        search_uom = self.env['product.uom'].search([('name','=',row[3] )], limit = 1) 
                                        if search_uom:
                                            vals.update({'product_uom' : search_uom.id })
                                        else:
                                            skipped_line_no[str(counter)]= " - Unidad de medida no encontrada. " 
                                            counter = counter + 1
                                            continue
                                    
                                    if row[4] in (None,""):
                                        vals.update({'price_unit' : search_product.standard_price })
                                    else:
                                        vals.update({'price_unit' : row[4] })
                                        
                                    if row[5].strip() in (None,"") and search_product.supplier_taxes_id:
                                        vals.update({'taxes_id' : [(6, 0, search_product.supplier_taxes_id.ids)]})
                                    else:
                                        taxes_list = []
                                        some_taxes_not_found = False
                                        for x in row[5].split(','):
                                            x = x.strip()
                                            if x != '':
                                                search_tax = self.env['account.tax'].search([('name','=',x)], limit = 1)
                                                if search_tax:
                                                    taxes_list.append(search_tax.id)
                                                else:
                                                    some_taxes_not_found = True
                                                    skipped_line_no[str(counter)]= " - Impuesto " + x +  " no encontrado. "                                                 
                                                    break  
                                        if some_taxes_not_found:
                                            counter = counter + 1
                                            continue
                                        else:
                                            vals.update({'taxes_id' : [(6, 0, taxes_list)]})
                                    
                                    if row[6] in (None,""):
                                        vals.update({'date_planned' : datetime.now()})
                                    else:
                                        cd = row[6]                
                                        cd = str(datetime.strptime(cd, '%Y-%m-%d').date())
                                        vals.update({"date_planned" : cd})

                                    #DESTINO
                                    if row[7] in (None,""):
                                        continue
                                    else:
                                        search_destino = self.env['stock.location'].search([('complete_name','like',row[7])], limit = 1)
                                        if search_destino:
                                            vals.update({'location_dest_id' : search_destino.id})
                                        else:
                                            skipped_line_no[str(counter)]= " - Destino no encontrada. " 
                                            counter = counter + 1
                                            continue  
                                        
                                else:
                                    skipped_line_no[str(counter)]= " - Producto no encontrado. " 
                                    counter = counter + 1 
                                    continue

                                ### search_destino = self.env['stock.location'] <<<<<<TRABAJANDO
                                
                                vals.update({'order_id' : self.env.context.get('sh_po_id')})
                                
                                created_pol = pol_obj.create(vals)
                                counter = counter + 1
                            
                            else:
                                skipped_line_no[str(counter)] = " - Product is empty. "  
                                counter = counter + 1      
                        
                        except Exception as e:
                            skipped_line_no[str(counter)] = " - El valor no es valido " + ustr(e)   
                            counter = counter + 1 
                            continue          
                             
                except Exception:
                    raise UserError(_("Lo sentimos, su archivo csv no coincide con nuestro formato"))
                 
                if counter > 1:
                    completed_records = (counter - len(skipped_line_no)) - 2
                    res = self.show_success_msg(completed_records, skipped_line_no)
                    return res
 
             
            #For Excel
            if self.import_type == 'excel':
                counter = 1
                skipped_line_no = {}                  
                try:
                    wb = xlrd.open_workbook(file_contents=base64.decodestring(self.file))
                    sheet = wb.sheet_by_index(0)     
                    skip_header = True    
                    for row in range(sheet.nrows):
                        try:
                            if skip_header:
                                skip_header = False
                                counter = counter + 1
                                continue
                            
                            if sheet.cell(row,0).value != '': 
                                vals={}
                                
                                field_nm = 'name'
                                if self.product_by == 'name':
                                    field_nm = 'name'
                                elif self.product_by == 'int_ref':
                                    field_nm = 'default_code'
                                elif self.product_by == 'barcode':
                                    field_nm = 'barcode'
                                
                                search_product = self.env['product.product'].search([(field_nm,'=',sheet.cell(row,0).value )], limit = 1)
                                if search_product:
                                    vals.update({'product_id' : search_product.id})
                                    
                                    if sheet.cell(row,1).value != '':
                                        vals.update({'name' : sheet.cell(row,1).value })
                                    else:
                                        vals.update({'name' : search_product.name})
                                        
                                        active_po = self.env['purchase.order'].search([('id','=',self.env.context.get('sh_po_id'))])
                                        if active_po:
                                            product_lang = search_product.with_context({
                                                'lang': active_po.partner_id.lang,
                                                'partner_id': active_po.partner_id.id,
                                            })
                                            pro_desc = product_lang.display_name
                                            if product_lang.description_purchase:
                                                pro_desc += '\n' + product_lang.description_purchase 
                                            vals.update({'name' : pro_desc})                                       

                                    if sheet.cell(row,2).value != '':
                                        vals.update({'product_qty' : sheet.cell(row,2).value })
                                    else:
                                        vals.update({'product_qty' : 1 })
                                    
                                    if sheet.cell(row,3).value in (None,"") and search_product.uom_po_id:
                                        vals.update({'product_uom' : search_product.uom_po_id.id })
                                    else:
                                        search_uom = self.env['product.uom'].search([('name','=',sheet.cell(row,3).value )], limit = 1) 
                                        if search_uom:
                                            vals.update({'product_uom' : search_uom.id })
                                        else:
                                            skipped_line_no[str(counter)]= " - Unidad de medida no encontrada. " 
                                            counter = counter + 1
                                            continue
                                    
                                    if sheet.cell(row,4).value in (None,""):
                                        vals.update({'price_unit' : search_product.standard_price })
                                    else:
                                        vals.update({'price_unit' : sheet.cell(row,4).value })
                                        
                                    if sheet.cell(row,5).value.strip() in (None,"") and search_product.supplier_taxes_id:
                                        vals.update({'taxes_id' : [(6, 0, search_product.supplier_taxes_id.ids)]})
                                    else:
                                        taxes_list = []
                                        some_taxes_not_found = False
                                        for x in sheet.cell(row,5).value.split(','):
                                            x = x.strip()
                                            if x != '':
                                                search_tax = self.env['account.tax'].search([('name','=',x)], limit = 1)
                                                if search_tax:
                                                    taxes_list.append(search_tax.id)
                                                else:
                                                    some_taxes_not_found = True
                                                    skipped_line_no[str(counter)]= " - Impuesto " + x +  " no encontrado. "                                                 
                                                    break  
                                        if some_taxes_not_found:
                                            counter = counter + 1
                                            continue
                                        else:
                                            vals.update({'taxes_id' : [(6, 0, taxes_list)]})
                                    
                                    if sheet.cell(row,6).value in (None,""):
                                        vals.update({'date_planned' : datetime.now()})
                                    else:
                                        cd = sheet.cell(row,6).value               
                                        cd = str(datetime.strptime(cd, '%Y-%m-%d').date())
                                        vals.update({"date_planned" : cd})

                                    #DESTINO
                                    if sheet.cell(row,7).value != None or sheet.cell(row,7).value != "":
                                        search_destino = self.env['stock.location'].search([('complete_name','like', sheet.cell(row,7).value)], limit = 1)
                                        if search_destino:
                                            vals.update({'location_dest_id' : search_destino.id})
                                        else:
                                            skipped_line_no[str(counter)]= " - Destino no encontrada. " 
                                            counter = counter + 1
                                            continue    
                                        
                                else:
                                    skipped_line_no[str(counter)]= " - Producto no encontrado. " 
                                    counter = counter + 1 
                                    continue
                                
                                vals.update({'order_id' : self.env.context.get('sh_po_id')})
                                
                                created_pol = pol_obj.create(vals)
                                counter = counter + 1
                            
                            else:
                                skipped_line_no[str(counter)] = " - Product is empty. "  
                                counter = counter + 1      
                        
                        except Exception as e:
                            skipped_line_no[str(counter)] = " - El valor no es valido " + ustr(e)   
                            counter = counter + 1 
                            continue          
                             
                except Exception:
                    raise UserError(_("Lo sentimos, su archivo de excel no coincide con nuestro formato"))
                 
                if counter > 1:
                    completed_records = (counter - len(skipped_line_no)) - 2
                    res = self.show_success_msg(completed_records, skipped_line_no)
                    return res


class sh_message_wizard(models.TransientModel):
    _name="sh.message.wizard"
    
    def get_default(self):
        if self.env.context.get("message",False):
            return self.env.context.get("message")
        return False 

    name=fields.Text(string="Mensaje",readonly=True,default=get_default)