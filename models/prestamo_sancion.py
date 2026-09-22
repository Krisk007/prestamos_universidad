from odoo import fields, models


class PrestamoSancion(models.Model):
    _name = 'prestamo.sancion'
    _description = 'Sancion de prestamo'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'fecha desc, id desc'

    name = fields.Char(string='Motivo', required=True, tracking=True)
    prestatario_id = fields.Many2one(
        'res.users',
        string='Usuario',
        required=True,
        tracking=True,
        domain=[('prestamo_perfil', '!=', False)],
    )
    prestamo_id = fields.Many2one('prestamo.prestamo', string='Prestamo')
    tipo = fields.Selection(
        [('atraso', 'Atraso'), ('dano', 'Dano'), ('perdida', 'Perdida'), ('otro', 'Otro')],
        string='Tipo',
        required=True,
        default='atraso',
        tracking=True,
    )
    fecha = fields.Datetime(string='Fecha', default=fields.Datetime.now, required=True)
    dias_sancion = fields.Integer(string='Dias de sancion', default=1)
    monto = fields.Monetary(string='Monto')
    currency_id = fields.Many2one('res.currency', string='Moneda', default=lambda self: self.env.company.currency_id)
    descripcion = fields.Text(string='Descripcion')
    state = fields.Selection(
        [('activa', 'Activa'), ('cumplida', 'Cumplida'), ('cancelada', 'Cancelada')],
        string='Estado',
        default='activa',
        required=True,
        tracking=True,
    )

    def action_cumplir(self):
        self.write({'state': 'cumplida'})

    def action_cancelar(self):
        self.write({'state': 'cancelada'})
