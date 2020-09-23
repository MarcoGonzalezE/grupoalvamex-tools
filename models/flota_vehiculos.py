# -*- coding: utf-8 -*-

from odoo import fields, models, api, _

class FleetVehicle(models.Model):
	_inherit = 'fleet.vehicle'

	vehicle_assign = fields.One2many('fleet.vehicle.assignments', 'vehicle_id', string="Historial de Asignaciones")
	date_assign = fields.Date(string="Fecha de Asignacion")
	assign_id = fields.Many2one('fleet.vehicle.assignments', string="Asignacion ID")
	state_id = fields.Many2one()
	driver_id = fields.Many2one()

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
		self.driver_id = False
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
		self.driver_id = self.assign_id.driver_id
		self.date_assign = self.assign_id.date_assign



class FleetVehicleAssignments(models.Model):
	_name = 'fleet.vehicle.assignments'

	vehicle_id = fields.Many2one('fleet.vehicle', string="Vehiculo")
	driver_id = fields.Many2one('res.partner', string="Conductor")
	driver_job = fields.Char(string="Puesto de Trabajo")
	date_assign = fields.Date(string="Fecha de Asignacion")
	date_return = fields.Date(string="Fecha de Devolucion")
	note = fields.Text(string="Notas")

	def assign_vehicle(self):
		assignments = self.env['fleet.vehicle.assignments'].search([],order='id desc')[0]
		self.vehicle_id.assign_id = assignments.id
		self.vehicle_id.driver_id = assignments.driver_id
		self.vehicle_id.date_assign = assignments.date_assign

	@api.multi
	def save(self):
		return True
