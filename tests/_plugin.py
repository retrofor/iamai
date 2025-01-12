# plugin.py

def register(engine):
    @engine.rule('start')
    def _(m):
        engine.ruleset('expense')
        @engine.when_all(lambda m: m.subject == 'approve' or m.subject == 'ok')
        def approved(c):
            print('Approved subject: {0}'.format(c.m.subject))

    engine.set_current_ruleset('start')
    engine >> 'continue'