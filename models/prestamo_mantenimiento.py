from odoo import fields, models


class PrestamoMantenimiento(models.Model):
    _name = 'prestamo.mantenimiento'
    _description = 'Mantenimiento de recurso'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'fecha_inicio desc, id desc'

    name = fields.Char(string='Referencia', required=True, tracking=True)
    recurso_id = fields.Many2one('prestamo.recurso', string='Recurso', required=True, tracking=True)
    area_id = fields.Many2one(related='recurso_id.area_id', string='Area responsable', store=True, readonly=True)
    fecha_inicio = fields.Date(string='Fecha inicio', default=fields.Date.context_today, required=True)
    fecha_fin = fields.Date(string='Fecha fin')
    responsable_id = fields.Many2one('res.users', string='Responsable', default=lambda self: self.env.user)
    descripcion = fields.Text(string='Descripcion')
    resultado = fields.Text(string='Resultado')
    state = fields.Selection(
        [
            ('programado', 'Programado'),
            ('proceso', 'En proceso'),
            ('finalizado', 'Finalizado'),
            ('cancelado', 'Cancelado'),
        ],
        string='Estado',
        default='programado',
        tracking=True,
        required=True,
    )

    def action_iniciar(self):
        self.write({'state': 'proceso'})

    def action_finalizar(self):
        self.write({'state': 'finalizado', 'fecha_fin': fields.Date.context_today(self)})

    def action_cancelar(self):
        self.write({'state': 'cancelado'})
