from pages.models import Rolemodels
def random_rolemodel(request):
    random_rolemodel = Rolemodels.objects.order_by('?')[:1]
    for rolemodel in random_rolemodel:
        return {'random_rolemodel': rolemodel}