from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0014_alter_ato_efeito_votoplacar'),
    ]

    operations = [
        migrations.AddField(
            model_name='episodio',
            name='video_url',
            field=models.URLField(blank=True, max_length=500, verbose_name='vídeo 16:9 (URL externo, ImageTools)'),
        ),
        migrations.AddField(
            model_name='episodio',
            name='video_imagetools_uuid',
            field=models.CharField(blank=True, max_length=64, verbose_name='uuid do vídeo no ImageTools'),
        ),
    ]
