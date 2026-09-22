from odoo import fields, models


class PrestamoCategoria(models.Model):
    _name = 'prestamo.categoria'
    _description = 'Categoria de recurso'
    _order = 'name'

    name = fields.Char(string='Categoria', required=True)
    tipo = fields.Selection(
        [('libro', 'Libro'), ('equipo', 'Equipo'), ('otro', 'Otro')],
        string='Tipo',
        required=True,
        default='libro',
    )
    descripcion = fields.Text(string='Descripcion')
    active = fields.Boolean(default=True)
