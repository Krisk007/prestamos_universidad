from odoo import fields, models


class PrestamoDashboard(models.Model):
    _name = 'prestamo.dashboard'
    _description = 'Dashboard de prestamos universitarios'

    name = fields.Char(string='Nombre', default='Dashboard de prestamos')
    recursos_total = fields.Integer(string='Total de recursos', compute='_compute_counts')
    recursos_disponibles = fields.Integer(string='Recursos disponibles', compute='_compute_counts')
    recursos_prestados = fields.Integer(string='Recursos prestados', compute='_compute_counts')
    recursos_mantenimiento = fields.Integer(string='Recursos en mantenimiento', compute='_compute_counts')
    prestamos_activos = fields.Integer(string='Prestamos activos', compute='_compute_counts')
    prestamos_vencidos = fields.Integer(string='Prestamos vencidos', compute='_compute_counts')
    sanciones_pendientes = fields.Integer(string='Sanciones pendientes', compute='_compute_counts')
    usuarios_con_prestamos = fields.Integer(string='Usuarios con prestamos', compute='_compute_counts')

    def _compute_counts(self):
        Recurso = self.env['prestamo.recurso']
        Prestamo = self.env['prestamo.prestamo']
        Sancion = self.env['prestamo.sancion']
        prestamos_no_cancelados = Prestamo.search([('state', '!=', 'cancelado')])
        usuarios = prestamos_no_cancelados.mapped('prestatario_id')
        values = {
            'recursos_total': Recurso.search_count([]),
            'recursos_disponibles': Recurso.search_count([('disponibilidad', '=', 'disponible')]),
            'recursos_prestados': Recurso.search_count([('disponibilidad', '=', 'prestado')]),
            'recursos_mantenimiento': Recurso.search_count([('disponibilidad', '=', 'mantenimiento')]),
            'prestamos_activos': Prestamo.search_count([('state', 'in', ['confirmado', 'entregado'])]),
            'prestamos_vencidos': Prestamo.search_count([('state', '=', 'atrasado')]),
            'sanciones_pendientes': Sancion.search_count([('state', '=', 'activa')]),
            'usuarios_con_prestamos': len(usuarios),
        }
        for record in self:
            for field_name, value in values.items():
                record[field_name] = value

    def _action(self, xmlid):
        self.ensure_one()
        return self.env['ir.actions.act_window']._for_xml_id('prestamos_universidad.%s' % xmlid)

    def action_open_recursos(self):
        return self._action('prestamo_recurso_action')

    def action_open_recursos_disponibles(self):
        return self._action('prestamo_reporte_disponibilidad_action')

    def action_open_recursos_prestados(self):
        action = self._action('prestamo_recurso_action')
        action['domain'] = [('disponibilidad', '=', 'prestado')]
        action['name'] = 'Recursos prestados'
        return action

    def action_open_mantenimiento(self):
        action = self._action('prestamo_recurso_action')
        action['domain'] = [('disponibilidad', '=', 'mantenimiento')]
        action['name'] = 'Recursos en mantenimiento'
        return action

    def action_open_prestamos_activos(self):
        return self._action('prestamo_reporte_prestamos_activos_action')

    def action_open_prestamos_vencidos(self):
        return self._action('prestamo_reporte_prestamos_atrasados_action')

    def action_open_sanciones(self):
        return self._action('prestamo_reporte_sanciones_pendientes_action')

    def action_open_usuarios_con_prestamos(self):
        action = self._action('prestamo_prestamo_action')
        action['domain'] = [('state', '!=', 'cancelado')]
        action['context'] = {'group_by': 'prestatario_id'}
        action['name'] = 'Usuarios con prestamos'
        return action
