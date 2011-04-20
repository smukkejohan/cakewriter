from pages.models import Rolemodels, Rolemodelpage
from django.shortcuts import render_to_response
from django.template import RequestContext

def all_rolemodels(request): 
    rolemodels = Rolemodels.objects.all() 
    rolemodelpage = Rolemodelpage.objects.all()  
    return render_to_response(
        'pages/rolemodels.html', {'rolemodels': rolemodels,'rolemodelpage':rolemodelpage},
        context_instance = RequestContext(request)
    )