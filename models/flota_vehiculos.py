# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from datetime import datetime

class FleetVehicle(models.Model):
	_inherit = 'fleet.vehicle'

	vehicle_assign = fields.One2many('fleet.vehicle.assignments', 'vehicle_id', string="Historial de Asignaciones")
	date_assign = fields.Date(string="Fecha de Asignacion")
	assign_id = fields.Many2one('fleet.vehicle.assignments', string="Asignacion ID")
	state_id = fields.Many2one()
	driver_id = fields.Many2one()
	employee_id = fields.Many2one('hr.employee', string="Conductor")
	license_state = fields.Selection([('activa', 'Licencia Vigente'), 
		('inactiva', 'Licencia Expirada'), 
		('pendiente', 'Licencia cerca de Expirar')], 
		string='Estado Licencia de Conductor', compute="_state_license")


	@api.multi
	def assign_vehicle(self):
		form_id = self.env.ref('grupoalvamex_tools.fleet_vehicle_assignments_view_form')
		state = self.env['fleet.vehicle.state'].search([('name','=','Asignado')]).id
		self.state_id = state

		return{
			'name': "Asignacion de Vehiculo",
			'type': 'ir.actions.act_window',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'fleet.vehicle.assignments',
			'view_id': form_id.id,
			'context': {'default_vehicle_id': self.id},
			'target': 'new'
		}

	@api.multi
	def return_vehicle(self):
		form_id = self.env.ref('grupoalvamex_tools.fleet_vehicle_return_view_form')
		state = self.env['fleet.vehicle.state'].search([('name','=','Disponible')]).id
		self.state_id = state
		self.employee_id = False
		self.date_assign = False
		return{
			'name': "Devolucion de Vehiculo",
			'type': 'ir.actions.act_window',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'fleet.vehicle.assignments',
			'view_id': form_id.id,
			'res_id': self.assign_id.id,
			'target': 'new'
		}

	@api.onchange('assign_id')
	def onchange_state(self):
		self.employee_id = self.assign_id.employee_id
		self.date_assign = self.assign_id.date_assign

	@api.depends('employee_id')
	def _state_license(self):
		for r in self:
			if r.employee_id:
				if r.employee_id.days_expire == 0:
					r.license_state = 'inactiva'
				if r.employee_id.days_expire > 0 and r.employee_id.days_expire < 21:
					r.license_state = 'pendiente'
				if r.employee_id.days_expire > 20:
					r.license_state = 'activa'



class FleetVehicleAssignments(models.Model):
	_name = 'fleet.vehicle.assignments'
	_rec_name = "employee_id"

	vehicle_id = fields.Many2one('fleet.vehicle', string="Vehiculo")
	driver_id = fields.Many2one('res.partner', string="Conductor")
	employee_id = fields.Many2one('hr.employee', string="Conductor")
	driver_job = fields.Char(string="Puesto de Trabajo")
	date_assign = fields.Date(string="Fecha de Asignacion")
	date_return = fields.Date(string="Fecha de Devolucion")
	note = fields.Text(string="Notas")

	def assign_vehicle(self):
		assignments = self.env['fleet.vehicle.assignments'].search([],order='id desc')[0]
		self.vehicle_id.assign_id = assignments.id
		self.vehicle_id.employee_id = assignments.employee_id
		self.vehicle_id.date_assign = assignments.date_assign

	@api.multi
	def save(self):
		return True

class HrEmployee(models.Model):
	_inherit = 'hr.employee'

	driver = fields.Boolean(string="Operador")
	driver_license = fields.Char(string="ID de Licencia")
	license_type = fields.Char(string="Tipo de Licencia")
	license_valid = fields.Date(string="Licencia Valida Desde")
	license_expiration = fields.Date(string="Fecha de Expiracion")
	days_expire = fields.Integer(string="Dias para Expirar", compute="_compute_days_to_expire")

	@api.depends('license_expiration')
	def _compute_days_to_expire(self):
		for r in self:
			date = datetime.now()
			if r.license_expiration:
				date = datetime.strptime(r.license_expiration, '%Y-%m-%d')
			now = datetime.now()
			delta = date - now
			r.days_expire = delta.days if delta.days > 0 else 0