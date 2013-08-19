from django.http import HttpResponse

from omeroweb.webclient.decorators import login_required, render_response

from utils import parse_path

def index(request):
    """
    Just a place-holder, base for creating urls etc
    """

    return HttpResponse("Welcome to webtagging")


@login_required()
@render_response()
def auto_tag(request, datasetId=None, conn=None, **kwargs):
    """
    List all the images in a table, with their names tokenised to create 
    suggestions for new tags.
    Indicate where these match existing tags etc.
    """

    def listTags(image):
        """ This should be in the BlitzGateway! """
        return [a for a in image.listAnnotations() if a.__class__.__name__ == "TagAnnotationWrapper"]

    # TODO: handle list of Image IDs. Currently we ONLY support Dataset
    if datasetId is not None:
        dataset = conn.getObject("Dataset", datasetId)
        images = list( dataset.listChildren() )
        images.sort(key=lambda img: img.getName().lower())

    # Need to build our table...

    # First go through all images, getting all the tokens
    tokens = []
    for image in images:
        name = image.getName()

        path_tokens, file_tokens, ext_tokens = parse_path(name)
        tokens.extend(path_tokens)
        tokens.extend(file_tokens)
        #TODO As mentioned below (about 40 lines) extension tags are ignored for now
        #tokens.extend(ext_tokens)

    # remove duplicates
    tokens = list(set(tokens))
    tokens.sort(key=lambda name: name.lower())


    # find which tokens match existing Tags
    tokenTags = []
    for token in tokens:

        # Skip zero length tokens
        if len(token) == 0:
            continue

        # Get all tags matching the token
        matchingTags = list(conn.getObjects("TagAnnotation", attributes={'textValue':token}))

        tags = []
        # For each of the matching tags
        for matchingTag in matchingTags:
            # Add dictionary of details
            tags.append({'name':matchingTag.getValue(), 'id':matchingTag.getId(), 'desc':matchingTag.getDescription()})

        tokenTagMap = {'name':token}

        # Assign the matching tags to the token dictionary (only if there are any)
        if len(tags) > 0:
            tokenTagMap['tags'] = tags

        # Add the token with any tag mappings to the list
        tokenTags.append(tokenTagMap)

    # Populate the images with details
    imageDetails = []
    for image in images:
        pathTokens, fileTokens, extTokens = parse_path(image.getName())
        #TODO allTokens needs to be controlled by some form elements, e.g. extension/directory support on/off
        # Potentially each list of tokens would be treated differently so searched separately 
        # Ignore extTokens for now
        allTokens = pathTokens + fileTokens

        # Create mapping of tags that exist already on this image (value : id)
        imageTags = {}
        for tag in listTags(image):
            imageTags[tag.getValue()] = tag.getId()
        imageTokens = []
        # For each token that exists (tokens from all images)
        for token in tokenTags:
            imageToken = {}
            # If the token is present in the image
            if token['name'] in allTokens:
                # Get the tags (if any) that are relevant
                if 'tags' in token:
                    tags = token['tags']
                    # If exactly 1 tag exists for this image
                    if len(tags) == 1:
                        # Mark the token as matched
                        imageToken['matched'] = True
                        # Mark the token for autoselect
                        imageToken['autoselect'] = True
            # If the tag is already on the image (not necessarily because it has a matching token)
            if token['name'] in imageTags:
                # Mark the token as selected
                imageToken['selected'] = True
            imageTokens.append(imageToken)


        imageDetail = {'name':image.getName(), 'tokens':imageTokens}
        imageDetails.append(imageDetail)


    # How this works:
    # tokenTags is a list of the tokens involved in all the images. These contain details of the tags that match
    # imageDetails is a list of the images, each one has details per-above tokens. e.g. If the token is matched,
    # has a tag already selected or if it should be auto-selected 

    print 'tokenTags: ', tokenTags          #PRINT
    print 'imageDetails: ', imageDetails    #PRINT
    # We only need to return a dict - the @render_response() decorator does the rest...
    context = {'template': 'webtagging/tags_from_names.html'}
    context['tokenTags'] = tokenTags
    context['imageDetails'] = imageDetails
    return context


@login_required()
@render_response()
def process_update(request, conn=None, **kwargs):
    context = {'template': 'webtagging/submitted.html'}
    return context
    
