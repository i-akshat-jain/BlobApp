import datetime
from django.shortcuts import render
from django.http import JsonResponse
from blobApp.models import Mention as m
from blobApp.models import Blob as b
from datetime import date
import gzip
from io import BytesIO
from azure.storage.blob import BlobServiceClient as bs
from django.db.models import Q
import requests
from django.conf import settings
import threading
from django.core.paginator import Paginator

def get_data_and_save(blob_name, start=None, end=None, mention_id=1):
    account_url = "https://invenicscasestudy.blob.core.windows.net/"
    container_name = "wiki"
    # clear all previous records form the mention and blob table
    if mention_id == 1:
        m.objects.all().delete()

    blob_name = blob_name+'.gz'
    try:
        # Get data from Azure Blob Storage and save to database
        blob_service_client = bs(account_url=account_url)
        global container_client
        container_client = blob_service_client.get_container_client(
            container_name)
        # Convert blob_list to a list to access the blobs
        blob_list = list(container_client.list_blobs())

        # blob_list = container_client.list_blobs()
        # mention_id = 1
        idForBlobTable = 0
        # blob_list = list(blob_list)
        for blob in blob_list:
            if blob.name == blob_name:
                print(blob.name, idForBlobTable)
                global found_blob
                found_blob = blob
                blob_client = container_client.get_blob_client(blob)
                blob_contents = blob_client.download_blob()

                # Uncompress the data
                compressed_data = BytesIO(blob_contents.content_as_bytes())
                unzipped_data = gzip.GzipFile(fileobj=compressed_data).read()
                # Set a range to read the compressed data to just 3000 lines
                unzipped_range_data = unzipped_data[start:end]

                byte_file = BytesIO(unzipped_range_data)

                if b.objects.filter(blob=blob.name).exists():
                    print("object exists")
                    blob_obj = b.objects.get(blob=blob.name)
                    # blob_id = blob_obj.id
                else:
                    # idForBlobTable += 1
                    blob_obj = b.objects.create(id=idForBlobTable, blob=blob.name, date=date.today(
                    ), time=datetime.datetime.now().time())
                mentionObject = []
                rank = 1

                for line in byte_file:
                    fields = line.decode('utf-8').strip().split('\t')
                    if fields[0] == 'MENTION':
                        mention = fields[1]
                        position = fields[2]
                        wiki_url = fields[3]
                        mentionObject.append(
                            m(id=mention_id, blob_id=blob_obj, mention=mention, position=position, wikipedia_url=wiki_url))

                        # Create bulk insert having 3000 records each time
                        if rank % 5000 == 0:
                            # Save the first 2000 mentions to the database
                            print("bulk insert", rank, mention_id)
                            m.objects.bulk_create(mentionObject)
                            mentionObject = []

                        mention_id += 1
                        rank += 1
                # to save the last list of leftover objectsz
                if mentionObject:
                    m.objects.bulk_create(mentionObject)

            else:
                print("blob not found")
                idForBlobTable += 1

    except Exception as e:
        print(e)

    return mention_id


def mention_list(request):
    
  mentions = m.objects.all()
  
  # Paginate mentions
  paginator = Paginator(mentions, 100)
  page_num = request.GET.get('page', 1)
  page = paginator.get_page(page_num)

  data = {
    'mentions': [serialize(m) for m in page], 
    'has_next_page': page.has_next()
  }

  return JsonResponse(data)

def serialize(mention):
  return {
    'mention': mention.mention,
    'position': mention.position,
    'wikipedia_url': mention.wikipedia_url,
  }



def home(request):
    context = {}
    if request.method == 'POST':
        blob_name = request.POST.get('blob_name')
        if blob_name:
            # Get the data and save to the database
            success = get_data_and_save(blob_name, 0, 100000, 1)
            if success > 1:
                context['message'] = 'Data stored successfully!'
            else:
                context['message'] = 'Failed to get data from Azure.'

    # Make an HTTP GET request to the mention_list API
    try:
        response = requests.get('http://127.0.0.1:8000/api/mention/')
        data = response.json()
        mentions = data.get('mentions', [])
        context['mentions'] = mentions
    except requests.RequestException:
        context['message'] = 'Failed to fetch data from the API.'

    # Load the remaining mentions in the background
    if request.method == 'POST':
        blob_name = request.POST.get('blob_name')
        if blob_name:
            threading.Thread(target=get_data_and_save, args=(
                blob_name, 100000, None, success+1,)).start()

    return render(request, 'blobApp/home.html', context)


   