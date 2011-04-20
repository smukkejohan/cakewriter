from django.utils.translation import ugettext_lazy as _
from django.db import models
from django.db.models import signals
from django.contrib.auth.models import User
from markdown import markdown
from django import forms
from django.core.urlresolvers import reverse
import difflib, string
import os
from settings import *
from tinymce.widgets import TinyMCE
from django.template.defaultfilters import slugify

from book.models import Chapter
def isTag(x): return x[0] == "<" and x[-1] == ">"
def html2list(x, b=0):
	mode = 'char'
	cur = ''
	output = []
	for c in x:
		if mode == 'tag':
			if c == '>': 
				if b: cur += ']'
				else: cur += c
				output.append(cur); cur = ''; mode = 'char'
			else: cur += c
		elif mode == 'char':
			if c == '<': 
				output.append(cur)
				if b: cur = '['
				else: cur = c
				mode = 'tag'
			elif c in string.whitespace: output.append(cur+c); cur = ''
			else: cur += c
	output.append(cur)
	return filter(lambda x: x is not '', output)
class ShouldHaveExactlyOneRootSlug(Exception):
    pass

class Article(models.Model):
    """Wiki article referring to Revision model for actual content.
       'slug' and 'parent' field should be maintained centrally, since users
       aren't allowed to change them, anyways.
    """
    
    title = models.CharField(max_length=512, verbose_name=_('Article title'),
                             blank=False)
    slug = models.SlugField(max_length=100, verbose_name=_('slug'),
                            help_text=_('Letters, numbers, underscore and hyphen.'
                                        ' Do not use reserved words \'create\','
                                        ' \'history\' and \'edit\'.'),
                            blank=True)
    chapter_related = models.ForeignKey(Chapter, verbose_name=_('Related Chapter'), blank=True, null=True)    
    created_by = models.ForeignKey(User, verbose_name=_('Created by'), blank=True, null=True)
    created_on = models.DateTimeField(auto_now_add = 1, editable=False)
    modified_on = models.DateTimeField(auto_now_add = 1, editable=False)
    parent = models.ForeignKey('self', verbose_name=_('Parent article slug'), 
                               help_text=_('Affects URL structure and possibly inherits permissions'),
                               null=True, blank=True)
    locked = models.BooleanField(default=False, verbose_name=_('Locked for editing'))
    permissions = models.ForeignKey('Permission', verbose_name=_('Permissions'),
                                    blank=True, null=True,
                                    help_text=_('Permission group'), editable=False)
    current_revision = models.OneToOneField('Revision', related_name='current_rev',
                                            blank=True, null=True, editable=True)
    related = models.ManyToManyField('self', verbose_name=_('Related articles'), symmetrical=True,
                                     help_text=_('Sets a symmetrical relation other articles'),
                                     blank=True, null=True, editable=False)
    def attachments(self):
        return ArticleAttachment.objects.filter(article__exact = self)

    @classmethod
    def get_root(cls):
        """Return the root article, which should ALWAYS exist..
        except the very first time the wiki is loaded, in which
        case the user is prompted to create this article."""
        try:
            return Article.objects.filter(parent__exact = None)[0]
        except:
            raise ShouldHaveExactlyOneRootSlug()

    def get_url(self):
        """Return the Wiki URL for an article"""
        if self.parent:
            return self.parent.get_url() + '/' + self.slug
        else:
            return self.slug

    def get_abs_url(self):
        """Return the absolute path for an article. This is necessary in cases
        where the template system isn't used for generating URLs..."""
        # TODO: Remove and create a reverse() lookup.
        return WIKI_BASE + self.get_url()

    @models.permalink
    def get_absolute_url(self):
        return ('wiki_view', [self.get_url()])

    @classmethod
    def get_url_reverse(cls, path, article, return_list=[]):
        """Lookup a URL and return the corresponding set of articles
        in the path."""
        if path == []:
            return return_list + [article]
        # Lookup next child in path
        try:
            a = Article.objects.get(parent__exact = article, slug__exact=str(path[0]))
            return cls.get_url_reverse(path[1:], a, return_list+[article])
        except Exception, e:
            return None
    
    def can_read(self, user):
        """ Check read permissions and return True/False."""
        if self.permissions:
            perms = self.permissions.can_read.all()
            return perms.count() == 0 or perms.filter(read__exact = user.id).count() > 0
        else:
            return self.parent.can_read(user) if self.parent else True

    def can_write(self, user):
        """ Check write permissions and return True/False."""
        if self.permissions:
            perms = self.permissions.can_write.all()
            return perms.count() == 0 or perms.filter(write__exact = user.id).count() > 0
        else:
            return self.parent.can_write(user) if self.parent else True

    def can_write_l(self, user):
        """Check write permissions and locked status"""
        return not self.locked and self.can_write(user)

    def can_attach(self, user):
        return self.can_write_l(user) and (WIKI_ALLOW_ANON_ATTACHMENTS or not user.is_anonymous())

    def __unicode__(self):
        if self.slug == '' and not self.parent:
            return unicode(_('Root article'))
        else:
            return self.get_url()
    
    class Meta:
        unique_together = (('slug', 'parent'),)
        verbose_name = _('Article')
        verbose_name_plural = _('Articles')

def get_attachment_filepath(instance, filename):
    """Store file, appending new extension for added security"""
    dir_ = WIKI_ATTACHMENTS + instance.article.get_url()
    dir_ = '/'.join(filter(lambda x: x!='', dir_.split('/')))
    if not os.path.exists(WIKI_ATTACHMENTS_ROOT + dir_):
        os.makedirs(WIKI_ATTACHMENTS_ROOT + dir_)
    return dir_ + '/' + filename + '.upload'

class ArticleAttachment(models.Model):
    article = models.ForeignKey(Article, verbose_name=_('Article'))
    file = models.FileField(max_length=255, upload_to=get_attachment_filepath, verbose_name=_('Attachment'))
    uploaded_by = models.ForeignKey(User, blank=True, verbose_name=_('Uploaded by'), null=True)
    uploaded_on = models.DateTimeField(auto_now_add = True, verbose_name=_('Upload date'))
    
    def download_url(self):
        return reverse('wiki_view_attachment', args=(self.article.get_url(), self.filename()))
    
    def filename(self):
        return '.'.join(self.file.name.split('/')[-1].split('.')[:-1])
    
    def get_size(self):
        try:
            size = self.file.size
        except OSError:
            size = 0
        return size

    def filename(self):
        return '.'.join(self.file.name.split('/')[-1].split('.')[:-1])
    
    def is_image(self):
        fname = self.filename().split('.')
        if len(fname) > 1 and fname[-1].lower() in WIKI_IMAGE_EXTENSIONS:
            return True
        return False
    
    def get_thumb(self):
        return self.get_thumb_impl(*WIKI_IMAGE_THUMB_SIZE)

    def get_thumb_small(self):
        return self.get_thumb_impl(*WIKI_IMAGE_THUMB_SIZE_SMALL)

    def mk_thumbs(self):
        self.mk_thumb(*WIKI_IMAGE_THUMB_SIZE, **{'force':True})
        self.mk_thumb(*WIKI_IMAGE_THUMB_SIZE_SMALL, **{'force':True})

    def mk_thumb(self, width, height, force=False):
        """Requires Python Imaging Library (PIL)"""
        if not self.get_size():
            return False
        
        if not self.is_image():
            return False
    
        base_path = os.path.dirname(self.file.path)
        orig_name = self.filename().split('.')
        thumb_filename = "%s__thumb__%d_%d.%s" % ('.'.join(orig_name[:-1]), width, height, orig_name[-1])
        thumb_filepath = "%s%s%s" % (base_path, os.sep, thumb_filename)
    
        if force or not os.path.exists(thumb_filepath):
            try:
                import Image
                img = Image.open(self.file.path)            
                img.thumbnail((width,height), Image.ANTIALIAS)
                img.save(thumb_filepath)
            except IOError:
                return False

        return True

    def get_thumb_impl(self, wth, height):
        """Requires Python Imaging Library (PIL)"""
        
        if not self.get_size():
            return False
        
        if not self.is_image():
            return False
    
        self.mk_thumb(width, height)
        
        orig_name = self.filename().split('.')
        thumb_filename = "%s__thumb__%d_%d.%s" % ('.'.join(orig_name[:-1]), width, height, orig_name[-1])
        thumb_url = settings.MEDIA_URL + WIKI_ATTACHMENTS + self.article.get_url() +'/' + thumb_filename
    
        return thumb_url

    def __unicode__(self):
        return self.filename()
    
class Revision(models.Model):
    
    article = models.ForeignKey(Article, verbose_name=_('Article'))
    revision_text = models.CharField(max_length=255, blank=True, null=True, 
                                     verbose_name=_('Description of change'))
    revision_user = models.ForeignKey(User, verbose_name=_('Modified by'), 
                                      blank=True, null=True, related_name='wiki_revision_user')
    revision_date = models.DateTimeField(auto_now_add = True, verbose_name=_('Revision date'))
    contents = models.TextField(verbose_name=_('Contents (Use MarkDown format)'))
    contents_parsed = models.TextField(editable=False, blank=True, null=True)
    counter = models.IntegerField(verbose_name=_('Revision#'), default=1, editable=False)
    previous_revision = models.ForeignKey('self', blank=True, null=True, editable=True)
    
    def get_user(self):
        return self.revision_user if self.revision_user else _('Anonymous')
    
    def save(self, *args, **kwargs):
        # Check if contents have changed... if not, silently ignore save
        if self.article and self.article.current_revision:
            if self.article.current_revision.contents == self.contents:
                return
            else:
                import datetime
                self.article.modified_on = datetime.datetime.now()
                self.article.save()
        
        # Increment counter according to previous revision
        previous_revision = Revision.objects.filter(article=self.article).order_by('-counter')
        if previous_revision.count() > 0:
            if previous_revision.count() > previous_revision[0].counter:
                self.counter = previous_revision.count() + 1
            else:
                self.counter = previous_revision[0].counter + 1
        else:
            self.counter = 1
        self.previous_revision = self.article.current_revision

        # Create pre-parsed contents - no need to parse on-the-fly
        ext = WIKI_MARKDOWN_EXTENSIONS
        ext += ["wikilinks(base_url=%s/)" % reverse('wiki_view', args=('',))]
        self.contents_parsed = markdown(self.contents,
                                        extensions=ext,
                                        safe_mode='escape',)
        super(Revision, self).save(*args, **kwargs)
                
    def delete(self, **kwargs):
        """If a current revision is deleted, then regress to the previous
        revision or insert a stub, if no other revisions are available"""
        article = self.article
        if article.current_revision == self:
            prev_revision = Revision.objects.filter(article__exact = article,
                                                    pk__not = self.pk).order_by('-counter')
            if prev_revision:
                article.current_revision = prev_revision[0]
                article.save()
            else:
                r = Revision(article=article, 
                             revision_user = article.created_by)
                r.contents = unicode(_('Auto-generated stub'))
                r.revision_text= unicode(_('Auto-generated stub'))
                r.save()
                article.current_revision = r
                article.save()
        super(Revision, self).delete(**kwargs)
    
    
    def get_diff(self):
        out = []
        b = self.contents
        if self.previous_revision:
            a = self.previous_revision.contents
            a, b = html2list(a), html2list(b)
        else:
            a = self.contents
            a, b = html2list(a), html2list(b)
        s = difflib.SequenceMatcher(None, a, b)
    	for e in s.get_opcodes():
    		if e[0] == "replace":

    			out.append('<del>'+''.join(a[e[1]:e[2]]) + '</del><ins>'+''.join(b[e[3]:e[4]])+"</ins>")
    		elif e[0] == "delete":
    			out.append('<del class="diff">'+ ''.join(a[e[1]:e[2]]) + "</del>")
    		elif e[0] == "insert":
    			out.append('<ins class="diff">'+''.join(b[e[3]:e[4]]) + "</ins>")
    		elif e[0] == "equal":
    			out.append(''.join(b[e[3]:e[4]]))
    		else: 
    			raise "Um, something's broken. I didn't expect a '" + `e[0]` + "'."
    	return ''.join(out)	
    '''
                
    def get_diff(self):
        if self.previous_revision:
            previous = self.previous_revision.contents.splitlines(1)
        else:
            previous = []
        
        # Todo: difflib.HtmlDiff would look pretty for our history pages!
        diff = difflib.unified_diff(previous, self.contents.splitlines(1))
        # let's skip the preamble
        diff.next(); diff.next(); diff.next()
        
        for d in diff:
            yield d
    '''
    
    def __unicode__(self):
        return "r%d" % self.counter

    class Meta:
        verbose_name = _('article revision')
        verbose_name_plural = _('article revisions')

class Permission(models.Model):
    permission_name = models.CharField(max_length = 255, verbose_name=_('Permission name'))
    can_write = models.ManyToManyField(User, blank=True, null=True, related_name='write',
                                       help_text=_('Select none to grant anonymous access.'))
    can_read = models.ManyToManyField(User, blank=True, null=True, related_name='read',
                                       help_text=_('Select none to grant anonymous access.'))
    def __unicode__(self):
        return self.permission_name
    class Meta:
        verbose_name = _('Article permission')
        verbose_name_plural = _('Article permissions')

class RevisionForm(forms.ModelForm):
    contents = forms.CharField(label=_('Contents'), widget=TinyMCE(attrs={'rows':8, 'cols':50}))
    class Meta:
        model = Revision
        fields = ['contents', 'revision_text']
class RevisionFormWithTitle(forms.ModelForm):
    title = forms.CharField(label=_('Title'))
    class Meta:
        model = Revision
        fields = ['title', 'contents', 'revision_text']
class CreateArticleForm(RevisionForm):
    title = forms.CharField(label=_('Title'))
    class Meta:
        model = Revision
        fields = ['title', 'contents',]

def set_revision(sender, *args, **kwargs):
    """Signal handler to ensure that a new revision is always chosen as the
    current revision - automatically. It simplifies stuff greatly. Also
    stores previous revision for diff-purposes"""
    instance = kwargs['instance']
    created = kwargs['created']
    if created and instance.article:
        instance.article.current_revision = instance
        instance.article.save()

signals.post_save.connect(set_revision, Revision)

from book.models import Chapter
from datetime import datetime
def create_article(sender, **kwargs):
    chapter = kwargs.get('instance')
    created = kwargs.get('created')
    if created:
        article = Article(title=chapter.title,
                        slug=slugify(chapter.title),
                        chapter_related=chapter,
                        created_by=chapter.author,
                        created_on=datetime.now(),
                        modified_on=datetime.now(),
                        parent=Article.get_root())
        article.save()
        revision = Revision(article=article,
                            revision_user=chapter.author,
                            revision_date=datetime.now(),
                            contents=chapter.body_html,
                            contents_parsed=chapter.body_html,
                            counter=1)
        revision.save()
        article_with_rev = Article(pk=article.pk,
                                title=article.title,
                                slug=article.slug,
                                chapter_related=article.chapter_related,
                                created_by=article.created_by,
                                created_on=article.created_on,
                                modified_on=article.modified_on,
                                parent=article.parent,
                                current_revision=revision)
        article_with_rev.save()
signals.post_save.connect(create_article, sender=Chapter)
