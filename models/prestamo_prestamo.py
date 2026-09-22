from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class PrestamoPrestamo(models.Model):
    _name = 'prestamo.prestamo'
    _description = 'Prestamo universitario'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'fecha_solicitud desc, id desc'

    name = fields.Char(string='Referencia', required=True, copy=False, default='Nuevo', readonly=True)
    prestatario_id = fields.Many2one(
        'res.users',
        string='Usuario',
        required=True,
        tracking=True,
        domain=[('prestamo_perfil', '!=', False)],
    )
    area_id = fields.Many2one('prestamo.area', string='Area responsable', required=True, tracking=True)
    fecha_solicitud = fields.Datetime(string='Fecha de solicitud', default=fields.Datetime.now, required=True)
    fecha_entrega = fields.Datetime(string='Fecha de entrega', tracking=True)
    fecha_limite = fields.Datetime(string='Fecha limite', required=True, tracking=True)
    fecha_devolucion = fields.Datetime(string='Fecha de devolucion', tracking=True)
    line_ids = fields.One2many('prestamo.prestamo.line', 'prestamo_id', string='Detalle', copy=True)
    state = fields.Selection(
        [
            ('borrador', 'Borrador'),
            ('confirmado', 'Confirmado'),
            ('entregado', 'Entregado'),
            ('devuelto', 'Devuelto'),
            ('atrasado', 'Atrasado'),
            ('cancelado', 'Cancelado'),
        ],
        string='Estado',
        default='borrador',
        tracking=True,
        required=True,
    )
    observaciones = fields.Text(string='Observaciones')
    sancion_ids = fields.One2many('prestamo.sancion', 'prestamo_id', string='Sanciones')
    sanciones_count = fields.Integer(compute='_compute_sanciones_count', string='Sanciones')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nuevo') == 'Nuevo':
                vals['name'] = self.env['ir.sequence'].next_by_code('prestamo.prestamo') or 'Nuevo'
        return super().create(vals_list)

    @api.depends('sancion_ids', 'sancion_ids.state')
    def _compute_sanciones_count(self):
        for record in self:
            record.sanciones_count = len(record.sancion_ids)

    @api.constrains('fecha_solicitud', 'fecha_limite', 'fecha_devolucion')
    def _check_fechas(self):
        for record in self:
            if record.fecha_limite and record.fecha_solicitud and record.fecha_limite <= record.fecha_solicitud:
                raise ValidationError('La fecha limite debe ser posterior a la fecha de solicitud.')
            if record.fecha_devolucion and record.fecha_entrega and record.fecha_devolucion < record.fecha_entrega:
                raise ValidationError('La fecha de devolucion no puede ser anterior a la entrega.')

    def _check_can_confirm(self):
        for record in self:
            if not record.line_ids:
                raise UserError('Debe agregar al menos un recurso al prestamo.')
            if not record.prestatario_id.prestamo_perfil:
                raise UserError('El usuario debe tener un perfil universitario para prestamos.')
            if record.prestatario_id.prestamo_bloqueado or record.prestatario_id.prestamo_sanciones_activas:
                raise UserError('El usuario tiene bloqueo o sanciones activas.')
            recursos = record.line_ids.mapped('recurso_id')
            if len(recursos) != len(set(recursos.ids)):
                raise UserError('No puede repetir el mismo recurso dentro de un prestamo.')
            record.line_ids._check_resource_available()

    def action_confirmar(self):
        self._check_can_confirm()
        self.write({'state': 'confirmado'})

    def action_entregar(self):
        for record in self:
            record._check_can_confirm()
            fecha = fields.Datetime.now()
            record.write({'state': 'entregado', 'fecha_entrega': fecha})
            record.line_ids.write({'state': 'entregado', 'fecha_entrega': fecha})

    def action_devolver(self):
        for record in self:
            fecha = fields.Datetime.now()
            for line in record.line_ids.filtered(lambda l: l.state in ('entregado', 'atrasado')):
                line.write({
                    'state': 'devuelto',
                    'fecha_devolucion': fecha,
                    'estado_final': line.estado_final or line.estado_inicial,
                })
                line._crear_sancion_estado_final()
            if record.fecha_limite and fecha > record.fecha_limite:
                record._crear_sancion_atraso(fecha)
            record.write({'state': 'devuelto', 'fecha_devolucion': fecha})

    def action_cancelar(self):
        self.write({'state': 'cancelado'})
        self.line_ids.filtered(lambda l: l.state not in ('devuelto', 'cancelado')).write({'state': 'cancelado'})

    def action_marcar_atrasado(self):
        for record in self:
            if record.state == 'entregado':
                record.write({'state': 'atrasado'})
                record.line_ids.filtered(lambda l: l.state == 'entregado').write({'state': 'atrasado'})

    def _crear_sancion_atraso(self, fecha_devolucion):
        for record in self:
            exists = self.env['prestamo.sancion'].search([('prestamo_id', '=', record.id), ('tipo', '=', 'atraso')], limit=1)
            if not exists:
                dias = max((fecha_devolucion.date() - record.fecha_limite.date()).days, 1)
                self.env['prestamo.sancion'].create({
                    'name': 'Atraso en %s' % record.name,
                    'prestatario_id': record.prestatario_id.id,
                    'prestamo_id': record.id,
                    'tipo': 'atraso',
                    'fecha': fecha_devolucion,
                    'dias_sancion': dias,
                    'descripcion': 'Devolucion fuera de plazo.',
                })


class PrestamoPrestamoLine(models.Model):
    _name = 'prestamo.prestamo.line'
    _description = 'Detalle de prestamo'
    _order = 'id'

    prestamo_id = fields.Many2one('prestamo.prestamo', string='Prestamo', required=True, ondelete='cascade')
    recurso_id = fields.Many2one('prestamo.recurso', string='Recurso', required=True)
    categoria_id = fields.Many2one(related='recurso_id.categoria_id', string='Categoria', store=True, readonly=True)
    area_id = fields.Many2one(related='recurso_id.area_id', string='Area', store=True, readonly=True)
    estado_inicial = fields.Selection(
        [
            ('nuevo', 'Nuevo'),
            ('bueno', 'Bueno'),
            ('regular', 'Regular'),
            ('malo', 'Malo'),
        ],
        string='Estado inicial',
        required=True,
        default='bueno',
    )
    estado_final = fields.Selection(
        [
            ('nuevo', 'Nuevo'),
            ('bueno', 'Bueno'),
            ('regular', 'Regular'),
            ('malo', 'Malo'),
            ('danado', 'Danado'),
            ('perdido', 'Perdido'),
        ],
        string='Estado final',
    )
    fecha_entrega = fields.Datetime(string='Fecha de entrega')
    fecha_devolucion = fields.Datetime(string='Fecha de devolucion')
    observaciones = fields.Text(string='Observaciones')
    state = fields.Selection(
        [
            ('borrador', 'Borrador'),
            ('entregado', 'Entregado'),
            ('devuelto', 'Devuelto'),
            ('atrasado', 'Atrasado'),
            ('cancelado', 'Cancelado'),
        ],
        string='Estado',
        default='borrador',
        required=True,
    )

    @api.onchange('recurso_id')
    def _onchange_recurso_id(self):
        for line in self:
            if line.recurso_id:
                line.estado_inicial = line.recurso_id.estado_fisico

    @api.constrains('recurso_id', 'prestamo_id', 'state')
    def _check_recurso_unico_activo(self):
        for line in self:
            if not line.recurso_id or line.state in ('devuelto', 'cancelado'):
                continue
            domain = [
                ('id', '!=', line.id),
                ('recurso_id', '=', line.recurso_id.id),
                ('state', 'in', ['entregado', 'atrasado']),
            ]
            if self.search_count(domain):
                raise ValidationError('El recurso %s ya esta prestado.' % line.recurso_id.display_name)

    def _check_resource_available(self):
        for line in self:
            recurso = line.recurso_id
            if recurso.disponibilidad != 'disponible':
                raise UserError('El recurso %s no esta disponible.' % recurso.display_name)

    def _crear_sancion_estado_final(self):
        for line in self:
            if line.estado_final not in ('danado', 'perdido'):
                continue
            tipo = 'dano' if line.estado_final == 'danado' else 'perdida'
            exists = self.env['prestamo.sancion'].search([
                ('prestamo_id', '=', line.prestamo_id.id),
                ('tipo', '=', tipo),
                ('descripcion', 'ilike', line.recurso_id.display_name),
            ], limit=1)
            if not exists:
                self.env['prestamo.sancion'].create({
                    'name': '%s de %s' % ('Dano' if tipo == 'dano' else 'Perdida', line.recurso_id.display_name),
                    'prestatario_id': line.prestamo_id.prestatario_id.id,
                    'prestamo_id': line.prestamo_id.id,
                    'tipo': tipo,
                    'descripcion': 'Estado final reportado para el recurso %s.' % line.recurso_id.display_name,
                })
            if line.estado_final == 'danado':
                line.recurso_id.estado_fisico = 'malo'
            elif line.estado_final == 'perdido':
                line.recurso_id.estado_fisico = 'baja'
