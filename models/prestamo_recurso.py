from odoo import api, fields, models
from odoo.exceptions import ValidationError


class PrestamoRecurso(models.Model):
    _name = 'prestamo.recurso'
    _description = 'Recurso prestable'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char(string='Nombre del recurso', required=True, tracking=True)
    codigo = fields.Char(string='Codigo interno', required=True, tracking=True)
    tipo = fields.Selection(
        [('libro', 'Libro'), ('equipo', 'Equipo'), ('otro', 'Otro')],
        string='Tipo',
        required=True,
        default='libro',
        tracking=True,
    )
    categoria_id = fields.Many2one('prestamo.categoria', string='Categoria', required=True)
    area_id = fields.Many2one('prestamo.area', string='Area responsable', required=True)
    estado_fisico = fields.Selection(
        [
            ('nuevo', 'Nuevo'),
            ('bueno', 'Bueno'),
            ('regular', 'Regular'),
            ('malo', 'Malo'),
            ('baja', 'Baja'),
        ],
        string='Estado fisico',
        default='bueno',
        required=True,
        tracking=True,
    )
    disponibilidad = fields.Selection(
        [
            ('disponible', 'Disponible'),
            ('prestado', 'Prestado'),
            ('mantenimiento', 'En mantenimiento'),
            ('no_disponible', 'No disponible'),
        ],
        string='Disponibilidad',
        compute='_compute_disponibilidad',
        store=True,
    )
    active = fields.Boolean(default=True)
    autor = fields.Char(string='Autor')
    editorial = fields.Char(string='Editorial')
    isbn = fields.Char(string='ISBN')
    marca = fields.Char(string='Marca')
    modelo = fields.Char(string='Modelo')
    nro_serie = fields.Char(string='Numero de serie')
    ubicacion = fields.Char(string='Ubicacion')
    observaciones = fields.Text(string='Observaciones')
    prestamo_line_ids = fields.One2many('prestamo.prestamo.line', 'recurso_id', string='Historial de prestamos')
    mantenimiento_ids = fields.One2many('prestamo.mantenimiento', 'recurso_id', string='Mantenimientos')

    _sql_constraints = [
        ('codigo_unique', 'unique(codigo)', 'El codigo interno del recurso debe ser unico.'),
    ]

    @api.depends('active', 'estado_fisico', 'prestamo_line_ids.state', 'mantenimiento_ids.state')
    def _compute_disponibilidad(self):
        for record in self:
            if not record.active or record.estado_fisico == 'baja':
                record.disponibilidad = 'no_disponible'
            elif any(m.state in ('programado', 'proceso') for m in record.mantenimiento_ids):
                record.disponibilidad = 'mantenimiento'
            elif any(line.state in ('entregado', 'atrasado') for line in record.prestamo_line_ids):
                record.disponibilidad = 'prestado'
            else:
                record.disponibilidad = 'disponible'

    @api.constrains('tipo', 'categoria_id')
    def _check_categoria_tipo(self):
        for record in self:
            if record.categoria_id and record.categoria_id.tipo not in (record.tipo, 'otro'):
                raise ValidationError('La categoria seleccionada no corresponde al tipo del recurso.')
