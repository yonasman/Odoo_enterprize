from datetime import timedelta

from odoo import fields, models, api
from odoo.exceptions import UserError

class drogaanalyticext(models.Model):
    _inherit = 'account.analytic.account'
    project=fields.Many2one('project.project')
    profit_center=fields.Many2one('account.analytic.account',domain=[
        ('plan_id', '=', 'Cost Center')])

class droga_project_task_problems(models.Model):
    _name='project.task.problems'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    task=fields.Many2one('project.task')
    problem=fields.Char('Problem')
    severity = fields.Selection([('High', 'High'), ('Medium', 'Medium'),('Low','Low')])
    problem_date=fields.Date('Date occurred')
    proposed_solution=fields.Char('Proposed resolution')
    action_taken=fields.Char('Action taken')
    current_status=fields.Selection([('Open', 'Open'), ('In Progress', 'In Progress'),('Done','Done')],tracking=True)

class drogaSubTask(models.Model):
    _inherit = 'project.task'

    task_progress = fields.Float(compute='_task_weight', store=True)
    sum_of_tasks = fields.Float(compute='_task_weight', string="Sum Of Task weight", store=True)
    task_editable = fields.Boolean(compute='_compute_editable',search='_task_editable', store=True)
    task_weight = fields.Float(default=0)
    parent_stage=fields.Many2one('parent.task.type')
    contractor=fields.Many2one('res.partner')
    cost_center=fields.Many2one('account.analytic.account',domain=[('project', '=', False)])
    problems=fields.One2many('project.task.problems','task')
    predecessors = fields.One2many('droga.sub.task.predecessor', 'task')
    planned_date_begin = fields.Datetime("Start date", tracking=True, task_dependency_tracking=True,default=fields.date.today())
    task_description=fields.Char('Task Description')
    task_duration=fields.Integer('Task duration')
    consultants=fields.Many2many('droga.project.consultant')
    contractors = fields.Many2many('droga.project.contractors')

    @api.onchange('task_duration')
    def _compute_planned_end_date(self):
        if self.planned_date_begin and self.task_duration:
            self.planned_date_end = self.planned_date_begin + timedelta(days=self.task_duration)

    @api.onchange('planned_date_begin','planned_date_end')
    def _compute_task_duration(self):
        if self.planned_date_begin and not self.planned_date_end:
            self.planned_date_end = self.planned_date_begin + timedelta(days=self.task_duration)
        if self.planned_date_begin and self.planned_date_end:
            self.task_duration = abs((self.planned_date_begin - self.planned_date_end).days)

    @api.depends('child_ids')
    def _compute_editable(self):
        for rec in self:
            if rec.child_ids:
                rec.task_editable = False
            else:
                rec.task_editable = True

    def _task_editable(self, operator, value):
        if operator == '=':
            tasks = self.env['project.task'].search([('child_ids', '=', False)])
            if len(tasks) == 0:
                has_childs = self.env['project.task'].sudo().search([('child_ids', '=', False)])
                return [('id', 'in', [x.id for x in has_childs] if has_childs else False)]
            else:
                return [('id', 'in', [])]
        else:
            return [('id', 'in', [])]

    @api.constrains('sum_of_tasks')
    def _check_subtask_weight_sum(self):
        for task in self:
            if task.child_ids:
                if task.sum_of_tasks > 100:
                    raise UserError('The sum of subtask weights cannot be greater than 100.')
                if task.sum_of_tasks < 100:
                    raise UserError('The sum of subtask weights cannot be less than 100.')
            #else:
            #    if task.task_weight < 100 or self.task_weight > 100:
            #        raise UserError('Task Weight must equal to 100')

    @api.depends('child_ids', 'child_ids.child_ids', 'child_ids.child_ids.child_ids',
                 'child_ids.child_ids.child_ids.child_ids', 'child_ids.child_ids.child_ids.child_ids.child_ids',
                 'child_ids.child_ids.child_ids.child_ids.child_ids.child_ids',
                 'child_ids.child_ids.child_ids.child_ids.child_ids.child_ids.child_ids',
                 'child_ids.task_weight', 'child_ids.child_ids.task_weight',
                 'child_ids.child_ids.child_ids.task_weight',
                 'child_ids.child_ids.child_ids.child_ids.task_weight',
                 'child_ids.child_ids.child_ids.child_ids.child_ids.task_weight',
                 'child_ids.child_ids.child_ids.child_ids.child_ids.child_ids.task_weight',
                 'child_ids.child_ids.child_ids.child_ids.child_ids.child_ids.child_ids.task_weight'
                 )
    def _task_weight(self):
        task_progress = 0.00000
        for record in self:
            record.task_progress = 0
            record.sum_of_tasks = 0
            for rec in record.child_ids:
                record.task_progress += (rec.task_weight * rec.task_progress) / 100
                record.sum_of_tasks += rec.task_weight
                if record.task_progress == 100:
                    self.stage_id.name = 'Development'

    def local_purchase(self):
        return {
            'name': 'Local Purchase',
            'view_type': 'tree',
            'view_mode': 'tree,form',
            'res_model': 'droga.purchase.request.local',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'context': {
                'default_subtask_reference': self.id,
                # 'default_issue_type': 'SIF'
            },
            'domain':
                ([('subtask_reference', '=', self.id)])
        }

    def tasks_prob(self):
        return {
            'name': 'Problems',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'project.task',
            'view_id': self.env.ref('droga_project.droga_report_tasks_list_form_problems').id,
            'type': 'ir.actions.act_window',
             'target': 'new',
            'res_id': self.id,
            'context': {
                'default_project': self.id,
            }
        }

    def transferRequest(self):
        return {
            'name': 'Transfer Request',
            'view_type': 'tree',
            'view_mode': 'tree,form',
            'res_model': 'droga.inventory.transfer.custom',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'context': {
                'default_stock_request_reference': self.id,
                # 'default_issue_type': 'SIF'
            },
            'domain':
                ([('stock_request_reference', '=', self.id)])
        }
    def stockRequestcont(self):
        return {
            'name': 'Stock request for contractor',
            'view_type': 'tree',
            'view_mode': 'tree,form',
            'res_model': 'droga.inventory.consignment.issue',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'context': {
                'default_stock_request_reference': self.id,
                'default_issue_type': 'PRC',
                'default_customer':self.contractor.id,
                'default_menu_from': 'PR'
            },
            'domain':
                ([('stock_request_reference', '=', self.id)])
        }

    def stockRequestint(self):
        return {
            'name': 'Stock request for internal',
            'view_type': 'tree',
            'view_mode': 'tree,form',
            'res_model': 'droga.inventory.consignment.issue',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'context': {
                'default_stock_request_reference': self.id,
                'default_issue_type': 'PRI',
                'default_customer':1,
                'default_menu_from':'PR'
            },
            'domain':
                ([('stock_request_reference', '=', self.id)])
        }

    def taskPaymentRequest(self):
        if not self.cost_center:
            raise UserError(
                "Cost center must be filled to initiate a payment request.")
        return {
            'name': 'Payment Request',
            'view_type': 'tree',
            'view_mode': 'tree,form',
            'res_model': 'droga.account.payment.request',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'context': {
                'default_task_payment_request_reference': self.id,
                'default_costc':self.cost_center.id,
                'default_department':45
                # 'default_issue_type': 'SIF'
            },
            'domain':
                ([('task_payment_request_reference', '=', self.id)])
        }
    def unlink_(self):
        raise UserError(
            "Tasks can't be deleted. Please archive them instead.")

class drogaSubTaskPredecessors(models.Model):
    _name='droga.sub.task.predecessor'
    task=fields.Many2one('project.task')
    pid=fields.Many2one('project.project',related='task.project_id')
    predecessor_task=fields.Many2one('project.task',domain="['&',('id','!=',task),('project_id', '=', pid)]",required=True)
    predecessor_type = fields.Selection([('ff', 'Finish-to-Finish'), ('ss', 'Start-to-Start'), ('fs', 'Finish-to-Start'),('sf','Start-to-Finish')],required=True)


class droga_subtask_local_purchase(models.Model):
    _inherit = 'purchase.order'

    subtask_reference = fields.Many2one('project.task', readonly=True)

class droga_subtask_local_purchase_req(models.Model):
    _inherit = 'droga.purchase.request.local'

    subtask_reference = fields.Many2one('project.task', readonly=True)

class droga_stock_request(models.Model):
    _inherit = 'droga.inventory.office.supplies.request'
    stock_request_reference = fields.Many2one('project.task', readonly=True)

class droga_stock_request_transfer(models.Model):
    _inherit = 'droga.inventory.transfer.custom'
    stock_request_reference = fields.Many2one('project.task', readonly=True)

class droga_stock_request_issue(models.Model):
    _inherit = 'droga.inventory.consignment.issue'
    stock_request_reference = fields.Many2one('project.task', readonly=True)

class droga_task_stage_progress(models.Model):
    _inherit = 'project.task.type'
    _rec_name='stage_descr'
    stage_descr=fields.Char('Stage',compute='get_stage_name')
    task_stage_weight = fields.Float()
    task_stage_progress = fields.Float(compute='_task_stage_progress')
    task_sum = fields.Float(compute='_task_stage_progress', string="Sum of Task Weight under this stage")
    from_project_auto=fields.Boolean(default=False)
    tasks=fields.One2many('project.task','stage_id',string='Tasks',domain=([('parent_id', '=', False)]))

    def get_stage_name(self):
        for rec in self:
            rec.stage_descr=rec.name +' : '+str(rec.task_stage_progress)+' %'

    def tasks_weight(self):
        return {
            'name': 'Tasks',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'project.task.type',
            'view_id': self.env.ref('droga_project.droga_project_stage_tasks_popup').id,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'res_id': self.id,
            'context': {
                'default_stage_id': self.id
            }
        }

    def _compute_child_tasks(self):
        for record in self:
            task_list = record.env['project.task'].search([('stage_id', '=', record.id), ('parent_id', '=', False)])
            record.tasks=task_list.ids
    @api.model
    def create(self, vals):
        res = super(droga_task_stage_progress, self).create(vals)
        if not res.from_project_auto:
            raise UserError("You can not create a stage manually.")
        return res

    def write(self, vals):
        res = super(droga_task_stage_progress, self).write(vals)
        #if 'project_ids' in vals or 'name' in vals or 'sequence' in vals:
            #raise UserError("You can not update task manually.")
        sum_tasks=0
        for task in self.tasks:
            sum_tasks=sum_tasks+task.task_weight
        if sum_tasks!=0 and sum_tasks!=100:
            raise UserError("Sum of tasks weight under stage should be 100.")
        return res

    def _task_stage_progress(self):
        for record in self:
            task_list = record.env['project.task'].search([('stage_id', '=', record.id), ('parent_id', '=', False)])
            record.task_stage_progress = 0
            record.task_sum=0
            if task_list:
                for rec in task_list:
                    record.task_stage_progress += (rec.task_progress * rec.task_weight) / 100
                    record.task_sum += rec.task_weight




class droga_task_payment_request(models.Model):
    _inherit = 'droga.account.payment.request'
    task_payment_request_reference = fields.Many2one('project.task', readonly=True)
