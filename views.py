from . import models
from ._builtin import Page, WaitPage
from otree.api import Currency as c, currency_range
from .models import Constants


class OnlyFirstStage(Page):
    def is_displayed(self):
        return self.round_number == 1


class Welcome(OnlyFirstStage):
    pass


class Waiting1(WaitPage):
    def is_displayed(self):
        return self.round_number == 1
    wait_for_all_groups = True
    body_text = "Espera a que continúe el experimento."


class Introduction(OnlyFirstStage):
    pass


class Questions(OnlyFirstStage):
    pass

    form_model = models.Player
    form_fields = [
        'q1_1',
        'q1_2',
        'q2_1',
        'q2_2']

    def q1_1_error_message(self, value):
        if (value != Constants.q1_1_answer):
            return "Respuesta incorrecta"

    def q1_2_error_message(self, value):
        if (value != Constants.q1_2_answer):
            return "Respuesta incorrecta"

    def q2_1_error_message(self, value):
        if (value != Constants.q2_1_answer):
            return "Respuesta incorrecta"

    def q2_2_error_message(self, value):
        if (value != Constants.q2_2_answer):
            return "Respuesta incorrecta"

    def q3_error_message(self, value):
        if (value != Constants.q3_answer):
            return "Respuesta incorrecta"


class QuestionsFeedback(OnlyFirstStage):
    pass

    q1_1_sol = Constants.q1_1_answer
    q1_2_sol = Constants.q1_2_answer
    q2_1_sol = Constants.q2_1_answer
    q2_2_sol = Constants.q2_2_answer
    q3_sol = Constants.q3_answer
    q3_respuesta = ""

    def vars_for_template(self):
        # q1
        if self.player.q1_1 == self.q1_1_sol:
            q1_1_class = 'success'
            q1_1_msg = 'Correcto'
        else:
            q1_1_class = 'danger'
            q1_1_msg = 'Incorrecto: 8 - 2 * 1 + 5 = 8 - 2 + 5 = 11'
        if self.player.q1_2 == self.q1_2_sol:
            q1_2_class = 'success'
            q1_2_msg = 'Correcto'
        else:
            q1_2_class = 'danger'
            q1_2_msg = 'Incorrecto: 8 - 2 * 5 + 1 = 8 - 10 + 1 = -1'

        # q2
        if self.player.q2_1 == self.q2_1_sol:
            q2_1_class = 'success'
            q2_1_msg = 'Correcto'
        else:
            q2_1_class = 'danger'
            q2_1_msg = 'Incorrecto: Si la catástrofe ocurre, todos los jugadores del grupo ganan 0'
        if self.player.q2_2 == self.q2_2_sol:
            q2_2_class = 'success'
            q2_2_msg = 'Correcto'
        else:
            q2_2_class = 'danger'
            q2_2_msg = 'Incorrecto: Si la catástrofe NO ocurre, cada jugador gana lo que tenga en su fondo privado'

        # q3
        if self.player.q3 == self.q3_sol:
            q3_class = 'success'
            q3_msg = 'Correcto'
        else:
            q3_class = 'danger'
            q3_msg = 'Incorrecto: Ambos contribuís con la misma cantidad (5), por lo que vuestro beneficio privado es 8 - 2 * 5 + 5 = 3'
        self.q3_respuesta = self.player._meta.get_field_by_name('q3')[0].choices[self.player.q3-1][1]

        return {
            'q1_1_quest': self.player._meta.get_field_by_name('q1_1')[0].verbose_name, 'q1_1_class': q1_1_class, 'q1_1_msg': q1_1_msg, 'q1_1_sol': self.q1_1_sol,
            'q1_2_quest': self.player._meta.get_field_by_name('q1_2')[0].verbose_name, 'q1_2_class': q1_2_class, 'q1_2_msg': q1_2_msg, 'q1_2_sol': self.q1_2_sol,
            'q2_1_quest': self.player._meta.get_field_by_name('q2_1')[0].verbose_name, 'q2_1_class': q2_1_class, 'q2_1_msg': q2_1_msg, 'q2_1_sol': self.q2_1_sol,
            'q2_2_quest': self.player._meta.get_field_by_name('q2_2')[0].verbose_name, 'q2_2_class': q2_2_class, 'q2_2_msg': q2_2_msg, 'q2_2_sol': self.q2_2_sol,
            'q3_quest': self.player._meta.get_field_by_name('q3')[0].verbose_name, 'q3_class': q3_class, 'q3_msg': q3_msg, 'q3_sol': 'Ambos obtendréis 3 puntos', 'q3_respuesta': self.q3_respuesta
        }


class Contribute(Page):
    form_model = models.Player
    form_fields = ['a']

    def vars_for_template(self):
        return {
            'endowment_round': ('%.2f' % round(self.player.endowment_round, 0)).replace(',', '.')
        }

    def a_choices(self):
        self.player.initialize()
        if self.player.role() == Constants.TYPE_RICH:
            choices_max = Constants.choices_rich
        else:
            choices_max = Constants.choices_poor

        choices = []
        for ch in choices_max:
            if ch[0] <= self.player.endowment:
                choices.append(ch)
        return choices

    def a_max(self):
        if self.player.endowment_round > self.player.endowment:
            return self.player.endowment_round
        else:
            return self.player.endowment

    #timeout_submission = {'contribution': c(form_model.endowment / 2)}


class Waiting(WaitPage):
    wait_for_all_groups = True
    body_text = "Espera a que continúe el experimento."


class ResultsWaitPage(WaitPage):
    def after_all_players_arrive(self):
        self.group.set_profit_round()

        if self.round_number == Constants.num_rounds:
            self.group.set_payoffs()
            for p in self.group.get_players():
                p.participant.vars['P'] = Constants.P
                p.participant.vars['random_catastrophe'] = self.group.random_catastrophe
                p.participant.vars['tau'] = Constants.tau
                p.participant.vars['private_fund'] = p.private_fund
                p.participant.vars['prevention_fund'] = self.group.prevention_fund
                #p.participant.vars['rand_catastrophe'] = self.group.random_catastrophe
                p.participant.vars['prevention'] = self.group.prevention
                p.participant.vars['catastrophe'] = self.group.catastrophe
                p.participant.vars['payoff'] = p.payoff

    #wait_for_all_groups = True
    body_text = "Espera a que decidan los demás jugadores."


class Results(Page):
    """Players payoff: How much each has earned"""


page_sequence = [
    Welcome,
    Waiting1,
    Introduction,
    Questions,
    #QuestionsFeedback,
    Waiting1,
    Contribute,
    Waiting,
    ResultsWaitPage,
    Results
]
