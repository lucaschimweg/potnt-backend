import uuid, json, sys, os

from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest, HttpResponseForbidden, HttpResponseServerError, FileResponse
from django.views.decorators.http import require_http_methods

from django import forms
from django.core import serializers
from django.forms.models import model_to_dict
from django.views.decorators.csrf import csrf_exempt

from .models import Pothole, Road, Tenant
from .config import image_path

import jwt


def authenticated(func):
    def wrapper(request, tenant, **kwargs):
        try:
            if tenant == None:
                return HttpResponseBadRequest()
                
            if "Authorization" not in request.headers:
                return HttpResponseForbidden("No authorization")

            decoded = jwt.decode(bytes(request.headers["Authorization"][7:], encoding='utf-8'), 'secret', algorithms=['HS256'])
            if "tenant" in decoded and decoded["tenant"] == tenant:
                try:
                    return func(request, tenant=tenant, **kwargs)
                except Exception as e:
                    return HttpResponseServerError
            else:
                return HttpResponseForbidden("No authorization")
        except Exception as e:
            print(e)
            return HttpResponseBadRequest("Error during authorization")
        
    return wrapper


class UploadFileForm(forms.Form):
    file = forms.FileField()


@csrf_exempt
@require_http_methods(["POST"])
def signup(request):
    try:
        body_unicode = request.body.decode('utf-8')
        body = json.loads(body_unicode)
        if Tenant.objects.filter(name=body["name"]).exists():
            print("already existing")
            return HttpResponseBadRequest("Tenant already existing")

        Tenant(body["name"], body["username"], "pw").save()

        our_jwt = jwt.encode({"tenant": body["name"]}, 'secret', algorithm='HS256')
        return JsonResponse({"bearerToken": our_jwt.decode('utf-8')})

    except Exception as e:
        print(e)
        return HttpResponseBadRequest(repr(e))


@csrf_exempt
@require_http_methods(["POST"])
def login(request, tenant):
    try:
        body_unicode = request.body.decode('utf-8')
        body = json.loads(body_unicode)
        obj = Tenant.objects.get(name=tenant, username=body["username"])

        #check password
        our_jwt = jwt.encode({"tenant": tenant}, 'secret', algorithm='HS256')
        return JsonResponse({"bearerToken": our_jwt.decode('utf-8')})

    except Exception as e:
        return HttpResponseBadRequest(repr(e))


@csrf_exempt
@require_http_methods(["POST"])
def pothole(request, tenant):
    try:
        body_unicode = request.body.decode('utf-8')
        body = json.loads(body_unicode)
        pothole = Pothole(uuid=uuid.uuid4(), depth=body['depth'], width=body['width'], length=body['length'], latitude=body['coordinates']['latitude'], longitude=body['coordinates']['longitude'], road=Road.objects.get(uuid=body["road"]["uuid"]), tenant=Tenant.objects.get(name=tenant))
        pothole.save()
        return JsonResponse(model_to_dict(pothole), safe=False)
        
    except Exception as e:
        print(e)
        return HttpResponse(json.dumps({'code':400}), content_type='application/json')


@csrf_exempt
@require_http_methods(["GET"])
@authenticated
def roadPotholes(request, tenant, uuidRoad):
    try:
        road = Road.objects.get(uuid=uuidRoad)
        road_data = model_to_dict(road)
        raw_data = serializers.serialize('python', Pothole.objects.all().filter(tenant=tenant, road=Road.objects.get(uuid=uuidRoad)))
        actual_data = [{
            "uuid": d['fields']['uuid'],
            "depth": d['fields']['depth'],
            "width": d['fields']['width'],
            "length": d['fields']['length'],
            "coordinates": {
                "latitude": d['fields']['latitude'],
                "longitude": d['fields']['longitude'],
            },
            "road": {
                "name": road_data["name"],
                "uuid": road_data["uuid"],
            },
            } for d in raw_data]
        return JsonResponse(actual_data, safe=False)
    except Exception as e:
        print("Error: {0}".format(e))
        return HttpResponseBadRequest()
    

@csrf_exempt
@require_http_methods(["GET", "POST"])
def roads(request, tenant):
    try:
        if request.method == 'GET':
            raw_data = serializers.serialize('python', Road.objects.all().filter(tenant=tenant))
            actual_data = [{
                "uuid": d['pk'],
                "name": d['fields']["name"]
             } for d in raw_data]
            return JsonResponse(actual_data, safe=False)

        if request.method == 'POST':
            @authenticated
            def handler(request, tenant):
                body = json.loads(request.body.decode('utf-8'))
                road = Road(uuid=uuid.uuid4(), name=body['name'], tenant=Tenant.objects.get(name=tenant))
                road.save()
                return JsonResponse(model_to_dict(road), safe=False)
            
            return handler(request, tenant)
    except Exception as e:
        print(e)
        return HttpResponseBadRequest()


@csrf_exempt
@require_http_methods(["PUT", "DELETE", "GET"])
@authenticated
def potholeWithUuid(request, tenant, uuidPothole):
    try:
        if request.method == 'PUT':
            body_unicode = request.body.decode('utf-8')
            body = json.loads(body_unicode)
            Pothole.objects.filter(tenant=Tenant.objects.get(name=tenant), uuid=uuidPothole).update(depth=body['depth'], width=body['width'], length=body['length'])
            return HttpResponse("OK")
        if request.method == 'DELETE':
            o = Pothole.objects.get(tenant=Tenant.objects.get(name=tenant), uuid=uuidPothole)
            uuid = o.uuid
            o.delete()
            if os.path.exists(f'{image_path}/{uuid}'):
                os.remove(f'{image_path}/{uuid}')
            return HttpResponse("OK")
        if request.method == 'GET':
            d = model_to_dict(Pothole.objects.get(uuid=uuidPothole, tenant=Tenant.objects.get(name=tenant)))
            road_data = model_to_dict(Road.objects.get(uuid=d["road"], tenant=Tenant.objects.get(name=tenant)))
            return JsonResponse({
                "uuid": d['uuid'],
                "depth": d['depth'],
                "width": d['width'],
                "length": d['length'],
                "coordinates": {
                    "latitude": d['latitude'],
                    "longitude": d['longitude'],
                },
                "road": {
                    "name": road_data["name"],
                    "uuid": road_data["uuid"],
                },
            })
    except Exception as e:
        print(e)
        return HttpResponseBadRequest()

    
@csrf_exempt
@require_http_methods(["GET", "POST"])
def potholeImage(request, tenant, uuidPothole):
    try:
        if request.method == 'POST':
            p = Pothole.objects.get(uuid=uuidPothole, tenant=Tenant.objects.get(name=tenant))
            form = UploadFileForm(request.POST, request.FILES)
            if form.is_valid():
                with open(f'{image_path}/{p.uuid}', 'wb+') as destination:
                    for chunk in request.FILES["file"].chunks():
                        destination.write(chunk)
                return HttpResponse("ok")
        else:
            p = Pothole.objects.get(uuid=uuidPothole, tenant=Tenant.objects.get(name=tenant))
            img = open(f'{image_path}/{p.uuid}', 'rb')
            return FileResponse(img)
            
        return HttpResponseBadRequest()
    except Exception as e:
        print(e)
        return HttpResponseBadRequest()

