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
import threading
from django.core.paginator import Paginator
from django.contrib import messages

def get_data_and_save(blob_name, start=None, end=None, mention_id=1):
    account_url = "https://invenicscasestudy.blob.core.windows.net/"
    container_name = "wiki"
    # clear all previous records form the mention table
    if mention_id == 1:
        m.objects.all().delete()
    blob_name = blob_name+'.gz'
    try:
        # Get data from Azure Blob Storage and save to database
        blob_service_client = bs(account_url=account_url)
        container_client = blob_service_client.get_container_client(
            container_name)
        # Convert blob_list to a list to access the blobs
        blob_list = list(container_client.list_blobs())

        idForBlobTable = 0
        # blob_list = list(blob_list)
        for blob in blob_list:
            if blob.name == blob_name:
                # print(blob.name, idForBlobTable)
                blob_client = container_client.get_blob_client(blob)
                blob_contents = blob_client.download_blob()

                # Unzip the data and get the length of the data
                compressed_data = BytesIO(blob_contents.content_as_bytes())
                unzipped_data = gzip.GzipFile(fileobj=compressed_data).read()
                data_length = len(unzipped_data)
                
                # Get the data in the range specified by the user
                start = 0 if start is None or start < 0 else min(
                    start, data_length)
                end = data_length if end is None or end > data_length else max(
                    end, 0)
                
                
                unzipped_range_data = unzipped_data[start:end]
                # Convert the data to bytes
                byte_file = BytesIO(unzipped_range_data)

                if b.objects.filter(blob=blob.name).exists():
                    # print("blob_obj exists")
                    blob_obj = b.objects.get(blob=blob.name)

                else:
                    blob_obj = b.objects.create(id=idForBlobTable, blob=blob.name, date=date.today(
                    ), time=datetime.datetime.now().time())
                    
                mentionObject = []
                count = 1
                # Read the data line by line
                for line in byte_file:
                    fields = line.decode('utf-8').strip().split('\t')
                    # Check if the line is a mention or not
                    if len(fields) >= 4 and fields[0] == 'MENTION':
                        mention = fields[1]
                        position = fields[2]
                        wiki_url = fields[3]
                        mentionObject.append(
                            m(id=mention_id, blob_id=blob_obj, mention=mention, position=position, wikipedia_url=wiki_url))

                        # Create and save bulk insert having 5000 records each time
                        if count % 5000 == 0:
                            m.objects.bulk_create(mentionObject)
                            mentionObject = []

                        mention_id += 1
                        count += 1
                    else:
                        continue
                    
                # To save the last list of leftover objectsz
                if mentionObject:
                    m.objects.bulk_create(mentionObject)
                    print("bulk created")

            else:
                print("blob not found")
                idForBlobTable += 1

    except Exception as e:
        print(e)

    return mention_id

# Function to send the data to frontend
def mention_list(request):

    search_term = request.GET.get('search_term')
    mentions = m.objects.order_by('id')
    blobs = b.objects.all()

    if search_term:
        # Filter mentions by search term
        mentions = mentions.filter(Q(mention__icontains=search_term) | Q(
            position__icontains=search_term) | Q(wikipedia_url__icontains=search_term))
    # Paginate mentions
    paginator = Paginator(mentions, 50)
    page_num = request.GET.get('page', 1)
    page = paginator.get_page(page_num)

    data = {
        'mentions': [serialize(m) for m in page],
        'has_next_page': page.has_next()
    }

    return JsonResponse(data)

# Function to send the data to frontend in a serialized form
def serialize(mention):
    return {
        'mention': mention.mention,
        'position': mention.position,
        'wikipedia_url': mention.wikipedia_url,
    }

# Function to get BlobName from frontend and call the get_data_and_save function
def home(request):
    context = {}
    success = 1  # Initialize success here
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

    # Load the remaining mentions in the background using Threads
    if request.method == 'POST':
        blob_name = request.POST.get('blob_name')
        if blob_name:
            # Start background thread
            threading.Thread(target=threaded_func, args=(
                blob_name, 100000, None, success+1,)).start()
    return render(request, 'blobApp/home.html', context)

# Intiating the background thread
def threaded_func(blob_name,start, end, mention_id):
    try:
        get_data_and_save(blob_name, start, end, mention_id)
    except Exception as e:
        print(e)

