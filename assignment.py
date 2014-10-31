from calais import Calais
import sys
import string
import codecs
import re

API_KEY = "t3d4ty47jkc7snnsmzt487qj"
calais = Calais(API_KEY)

def nl2p(s):
    """Add paragraphs to a text."""
    return u'\n'.join(u'<p>%s</p>' % p for p in re.compile(r'\n{1,}').split(s))

def to_wikipedia_url(topic):
    return 'http://en.wikipedia.org/wiki/' + string.replace(topic, ' ', '_')

def get_entity_url(entity_json):
    try: return entity_json['resolutions'][0]['id']
    except: return to_wikipedia_url(entity_json["name"])


"""
The function that converts text to HTML per the assignment. 

The behavior of this function is under-specified when entities overlap.
For example, for the phrase "President of the United States of America",
Calais parses three entities: 1) "President", 2) "United States of America", 
and 3) "President of the United States of America". In HTML, though, <a> tags
can't be nested. So any linking of "President of the United States of America"
precludes linking the other two entities. 

If the function were to output: 
<a>
    <a>President</a> of the <a>United States of America</a>
</a>

The browser would produce a DOM tree of:
<a></a><a>President</a> of the <a>United States of America</a>

That would make the first link invisible and unclickable. 

So, in the function below, I've decided to to output and link all entities in 
cases of overlap. I.e. the example becomes: 
<a>President</a><a>President of the United States of America</a><a>United States of America</a>.
This makes the text less readable (words are duplicated), but because the primary
purpose of this assignment is to test Calais' accuracy at identifying and linking
entities, I think it's more important here that every extracted entity be 
linked and discoverable in the output than it is that the text remain identical.
"""
def annotate_text(text, calais):
    entities = calais.analyze(text).entities
    entityUrls = {}
    instances = []
    annotated_text = ""
    last_offset = 0

    for index, entity in enumerate(entities):
        # store our custom data about each entity (namely, the url)
        entityUrls[index] = get_entity_url(entity)

        # add all instances of the to the instances array, with a property
        # on each instance (entityIndex) that tracks which entity this is
        # an instance of, so we can get thep proper url later.
        for instance in entity['instances']:
            instance["entityIndex"] = index
            instances.append(instance)


    # sort all the instances, so that it's simpler to go
    # through the text and replace them with links
    instances.sort(key=lambda it:it['offset'])

    # and do the replacement
    for instance in instances:
        # add unmodified the text between the (end of) the prior instance and this one.
        annotated_text += text[last_offset:instance['offset']]

        # link the instance
        instance_url = entityUrls[instance['entityIndex']] 
        annotated_text += '<a href="' + instance_url + '">' + instance['exact'] + '</a>'
        last_offset = instance['offset'] + instance['length']; 

    return annotated_text

# The python-calais module handles unicode strings by converting to ASCII,
# and converting unmappable characters to their XML equivalents. I.e. it does
# str.encode('ascii', 'xmlcharrefreplace'). We have to do the same on our
# input text, which we'll insist is utf-8, so the character indices line up.
text = (u"".join(codecs.getreader("utf-8")(sys.stdin))).encode('ascii', 'xmlcharrefreplace')
annotated_html = nl2p(annotate_text(text, calais))

# Send the result to stdout. 
# (And, even though it's not strictly required, add
# some HTML to make the thing readable in the browser.)
print "<html><body style='max-width:40em;line-height:1.6em'>"
print annotated_html
print "</body></html>"