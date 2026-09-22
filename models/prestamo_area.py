from odoo import fields, models


class PrestamoArea(models.Model):
    _name = 'prestamo.area'
    _description = 'Area responsable'
    _order = 'name'

    name = fields.Char(string='Area responsable', required=True)
    responsable_id = fields.Many2one('res.users', string='Responsable')
    email = fields.Char(string='Correo')
    telefono = fields.Char(string='Telefono')
    ubicacion = fields.Char(string='Ubicacion')
    active = fields.Boolean(default=True)
