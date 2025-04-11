# This creates a page that github will send a request to after a post request has been sent
# In short this will update the website

from django.http import HttpResponse
from django.views import View   
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import hmac
import hashlib
import subprocess
from .views import page_not_found



### COPIED FROM ANOTHER PROJECT ###
#  
def is_valid_signature(x_hub_signature, data, private_key):
    """checks to ensure that github signature is valid so that the website can update from github"""
    # x_hub_signature and data are from the webhook payload
    # private key is your webhook secret
    hash_algorithm, github_signature = x_hub_signature.split('=', 1)
    algorithm = hashlib.__dict__.get(hash_algorithm)
    encoded_key = bytes(private_key, 'latin-1')
    mac = hmac.new(encoded_key, msg=data, digestmod=algorithm)
    return hmac.compare_digest(mac.hexdigest(), github_signature)


def run_cmd():
    command = 'git clean --force -d -x; git reset --hard; git -C "/home/schedulingsolar/app" pull -v origin main;' # resets local changes and pulls new ones
    cmd_output = subprocess.run(command, shell=True, stdout=subprocess.PIPE, text=True).stdout
    return cmd_output
  

class UpdateServerResponse(HttpResponse):
    '''to perform an action after response close'''
    def close(self):
        super(UpdateServerResponse, self).close()
        command = "touch /var/www/schedulingsolar_pythonanywhere_com_wsgi.py"
        cmd_output = subprocess.run(command, shell=True, stdout=subprocess.PIPE, text=True).stdout
        print(cmd_output)
        

class GithubUpdate(View):
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(GithubUpdate, self).dispatch(request, *args, **kwargs)
    
    def post(self, request):
        """is run when we want the server to update the website"""
        x_hub_signature = request.headers.get('X-Hub-Signature')
        if not x_hub_signature: 
            return page_not_found(request, 'Server update was attempted')
        else:
            data = request.body
            if is_valid_signature(x_hub_signature, data, "J8x7]AOO^2SJ6i"): # the webhook token

                cmd_output = run_cmd()
                return UpdateServerResponse(cmd_output)
            else:
                return page_not_found(request, 'Server update was attempted')
    
    def get(self, request):
        return page_not_found(request, 'Server update was attempted') 

