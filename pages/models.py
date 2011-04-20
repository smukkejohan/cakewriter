from django.db import models
from markdown import markdown
from thumbs import ImageWithThumbsField
from django.utils.text import truncate_words

class Frontpage(models.Model):
    content = models.TextField()
    def __unicode__(self):
        return truncate_words(self.content,10)
    
class Editpage(models.Model):
    content = models.TextField()
    def __unicode__(self):
        return truncate_words(self.content,10)
    
class Rolemodelpage(models.Model):
    content = models.TextField()
    def __unicode__(self):
        return truncate_words(self.content,10)
        
class Rolemodels(models.Model):
    name = models.CharField(max_length=512)
    content = models.TextField()
    content_html = models.TextField(null=True, blank=True)
    picture = ImageWithThumbsField(upload_to="rolemodels/", blank=True, null=True, help_text="You don't have to worry about the pictures size. It will automatically resize if over 500 px wide", sizes=((130,120),(500,100000)))
    class Meta:
        ordering = ('name',)
        verbose_name = 'Rolemodels'
        verbose_name_plural = 'Rolemodels'
    def save(self, *args, **kwargs):             
        self.content_html = markdown(self.content)
        super(Rolemodels, self).save(*args, **kwargs)