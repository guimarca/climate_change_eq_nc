'''
from otree.api import (
    models, widgets, BaseConstants, BaseSubsession, BaseGroup, BasePlayer, BaseLink
    Currency as c, currency_range
)
import random
'''
from __future__ import division
from otree.db import models
from otree.constants import BaseConstants
from otree.models import BaseSubsession, BaseGroup, BasePlayer, BaseLink

from otree import widgets
from otree.common import Currency as c, currency_range
import random


doc = """
Climate change game a la Milinski + competition
"""


class Constants(BaseConstants):
    name_in_url = 'climate_change_eq_nc'
    players_per_group = 6
    num_rounds = 10

    num_rich_players = 2
    num_poor_players = players_per_group - num_rich_players

    endowment_initial_rich = c(60)
    endowment_initial_poor = c(30)

    endowment_round_rich = endowment_initial_rich/(num_rounds)
    endowment_round_poor = endowment_initial_poor/(num_rounds)

    choices_rich = [[0,'0'],[1,'1'],[2,'2'],[3,'3'],[4,'4'],[5,'5'],[6,'6']]
    choices_poor = [[0,'0'],[1,'1'],[2,'2'],[3,'3']]

    alpha1 = 2
    alpha2 = 1
    tau = c(120.0)
    P = 0.9

    p_pctg = P * 100
    one_minus_p_pctg = round(1 - P,1) * 100

    TYPE_POOR = 0
    TYPE_RICH = 1

    q1_1_answer = 5
    q1_2_answer = 2
    q2_1_answer = 0
    q2_2_answer = 100
    q3_answer = 3

    instructions_template = 'climate_change_eq_nc/Instructions.html'


class Subsession(BaseSubsession):
    def before_session_starts(self):
        if self.round_number == 1:
            self.group_randomly()
        else:
            self.group_like_round(1)

    def vars_for_admin_report(self):
        contributions = [p.a for p in self.get_players() if p.a is not None]
        return {
            'avg_contribution': sum(contributions)/len(contributions),
            'min_contribution': min(contributions),
            'max_contribution': max(contributions),
        }



class Group(BaseGroup):
    total_contribution = models.CurrencyField(initial=0.0) # in a round
    prevention_fund = models.CurrencyField() # in all rounds

    tau = models.FloatField()
    alpha1 = models.FloatField()
    alpha2 = models.FloatField()
    P = models.FloatField()

    prevention = models.IntegerField(initial=1)
    catastrophe = models.IntegerField(initial=0)

    random_catastrophe = models.FloatField()

    # Calculate final payoffs
    def set_payoffs(self):
        catastrophic_coefficient = 1
        self.random_catastrophe = random.random()

        if self.prevention_fund < self.tau:  # prevention amount not reached
            self.prevention = 0

            if self.random_catastrophe < self.P:  # catastrophe happens
                catastrophic_coefficient = 0
                self.catastrophe = 1

        for p in self.get_players():
            p.payoff = p.private_fund * catastrophic_coefficient

            if p.payoff < 0:
                p.payoff = 0

    # Calculate profits of a single round
    def set_profit_round(self):
        self.tau = Constants.tau
        self.P = Constants.P
        self.alpha1 = Constants.alpha1
        self.alpha2 = Constants.alpha2
        self.total_contribution = sum([p.a for p in self.get_players()])

        if self.round_number == 1:
            self.prevention_fund = self.total_contribution
        else:
            self.prevention_fund = self.in_round(self.round_number-1).prevention_fund + self.total_contribution

        for p in self.get_players():
            if self.round_number == 1:
                p.private_fund = 0
            else:
                p.private_fund = p.in_round(self.round_number - 1).private_fund
            p.profit = p.endowment_round - p.a

            p.private_fund += p.profit


class Player(BasePlayer):
    type = models.IntegerField()
    endowment_initial = models.CurrencyField()  # initial endowment
    endowment = models.CurrencyField()  # what remains from endowment_initial
    endowment_round = models.CurrencyField()  # in a round

    profit = models.CurrencyField(initial=0.0) # in a round
    private_fund = models.CurrencyField()  # in all rounds

    a = models.CurrencyField(
        doc="""The amount contributed by the player to the prevention fund""",
        #widget=widgets.SliderInput(attrs={'step': '1'})
        widget=widgets.RadioSelectHorizontal(),
    )

    q1_1 = models.CurrencyField(
        verbose_name="¿Cuáles son tus beneficios privados esta ronda si eres el B1?")
    q1_2 = models.CurrencyField(
        verbose_name="¿Cuáles son tus beneficios privados esta ronda si eres el A2?")
    q2_1 = models.CurrencyField(verbose_name="¿Cuántos puntos ganas si la catástrofe ocurre?")
    q2_2 = models.CurrencyField(verbose_name="¿Cuántos puntos ganas si la catástrofe NO ocurre?")
    q3 = models.PositiveIntegerField(
        verbose_name="3. Eres Jugador B. En una ronda contribuyes al fondo de prevención con 3 puntos. Si el otro jugador de tipo B de tu grupo también contribuye con 3 puntos, ¿Cuáles serán vuestros beneficios privados esta ronda?",
        widget=widgets.RadioSelect(),
        choices=[
            [1, 'Ambos obtendréis 0 puntos'],
            [2, 'Ambos obtendréis 6 puntos'],
            [3, 'Ambos obtendréis 3 puntos'],
            [4, 'Tú obtendrás 6 puntos y él 3 puntos']
        ],
    )

    def initialize(self):
        if self.role() == Constants.TYPE_RICH:
            self.endowment_initial = Constants.endowment_initial_rich
            self.type = Constants.TYPE_RICH
            self.endowment_round = Constants.endowment_round_rich
        else:
            self.endowment_initial = Constants.endowment_initial_poor
            self.type = Constants.TYPE_POOR
            self.endowment_round = Constants.endowment_round_poor

        self.endowment = self.endowment_initial - (self.round_number - 1)*self.endowment_round
        self.profit = 0.0


    def player_id(self):
        if self.role() == Constants.TYPE_POOR:
            return 'A'+repr(self.id_in_group)
        else:
            return 'B'+repr(self.id_in_group-4)


    def role(self):
        # from 1 to n_poor: poor (e.g.: 1, 2, 3, 4)
        if self.id_in_group <= Constants.num_poor_players:
            return Constants.TYPE_POOR
        else: # from n_poor to n_in_group: rich (e.g.: 5, 6)
            return Constants.TYPE_RICH


class Link(BaseLink):
    pass

