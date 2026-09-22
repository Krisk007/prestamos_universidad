from odoo import api, fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    prestamo_perfil = fields.Selection(
        [
            ('estudiante', 'Estudiante'),
            ('docente', 'Docente'),
            ('administrador', 'Administrador'),
        ],
        string='Perfil universitario',
    )
    prestamo_codigo = fields.Char(string='Codigo universitario')
    prestamo_documento = fields.Char(string='Documento')
    prestamo_unidad = fields.Char(string='Carrera/Unidad')
    prestamo_telefono = fields.Char(string='Telefono universitario')
    prestamo_bloqueado = fields.Boolean(string='Bloqueado para prestamos')
    prestamo_motivo_bloqueo = fields.Text(string='Motivo de bloqueo')
    prestamo_ids = fields.One2many('prestamo.prestamo', 'prestatario_id', string='Prestamos')
    prestamo_sancion_ids = fields.One2many('prestamo.sancion', 'prestatario_id', string='Sanciones')
    prestamo_sanciones_activas = fields.Integer(
        compute='_compute_prestamo_sanciones_activas',
        string='Sanciones activas',
    )

    @api.depends('prestamo_sancion_ids', 'prestamo_sancion_ids.state')
    def _compute_prestamo_sanciones_activas(self):
        for user in self:
            user.prestamo_sanciones_activas = len(user.prestamo_sancion_ids.filtered(lambda s: s.state == 'activa'))
