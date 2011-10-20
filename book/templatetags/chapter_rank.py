from django import template
from book.models import Chapter

register = template.Library()

class ChapterRankNote(template.Node):
    def __init__(self, chapter, context_var):
        self.chapter = chapter
        self.context_var = context_var

    def render(self, context):
        try:
            chapter = template.resolve_variable(self.chapter, context)
        except template.VariableDoesNotExist:
            return ''
        chapters = Chapter.objects.filter(visible=True).extra(select={'r': '((100/%s*rating_score/(rating_votes+%s))+100)/2' 
                                                                            % (Chapter.rating.range, 
                                                                                Chapter.rating.weight
                                                                                )}).order_by('-r')
        i=0
        for loopChapter in chapters:
            i+=1
            if chapter==loopChapter:
                context[self.context_var] = i
                return ''
        return ''

@register.tag(name='get_chapter_rank')
def do_chapter_rank(parser, token):
    bits = token.contents.split()
    if len(bits) != 4:
        raise template.TemplateSyntaxError("'%s' tag takes exactly three arguments" % bits[0])
    if bits[2] != 'as':
        raise template.TemplateSyntaxError("second argument to '%s' tag must be 'as'" % bits[0])
    return ChapterRankNote(bits[1], bits[3])