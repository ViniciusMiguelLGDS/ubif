from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.conf import settings
import os

# Gerenciador de Usuário Personalizado
class UsuarioManager(BaseUserManager):
    def create_user(self, email, nome, password=None):
        if not email:
            raise ValueError('O usuário deve ter um endereço de e-mail')
        user = self.model(email=self.normalize_email(email), nome=nome)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, nome, password=None):
        user = self.create_user(email, nome, password)
        user.is_admin = True
        user.save(using=self._db)
        return user

# Modelo de Usuário
class Usuario(AbstractBaseUser):
    nome = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    telefone = models.CharField(max_length=20, blank=True, null=True)
    foto = models.ImageField(upload_to='usuarios_fotos/', blank=True, null=True)  # Adiciona o campo de foto
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    theme_preference = models.BooleanField(default=True)

    objects = UsuarioManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nome']

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True

    @property
    def is_staff(self):
        return self.is_admin

    def delete(self, *args, **kwargs):
        """Remove a foto do diretório ao deletar o usuário"""
        if self.foto:
            foto_path = os.path.join(settings.MEDIA_ROOT, self.foto.name)
            if os.path.exists(foto_path):
                os.remove(foto_path)
        super().delete(*args, **kwargs)


# Modelo de Oferta de Carona
class OfertaCarona(models.Model):
    motorista = models.ForeignKey(Usuario, on_delete=models.PROTECT, related_name='ofertas')  # Protegido contra exclusão
    origem = models.CharField(max_length=100)
    destino = models.CharField(max_length=100)
    data_hora = models.DateTimeField()
    vagas_ofertadas = models.PositiveIntegerField(default=0)
    descricao = models.TextField(blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=[('aberta', 'Aberta'), ('encerrada', 'Encerrada'), ('cancelada', 'Cancelada')],
        default='aberta'
    )
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    def vagas_disponiveis(self):
        reservas_confirmadas = self.reservas.filter(status='confirmada').count()
        return self.vagas_ofertadas - reservas_confirmadas

    def __str__(self):
        return f"{self.origem} -> {self.destino} ({self.data_hora})"

# Modelo de Reserva de Carona
class ReservaCarona(models.Model):
    oferta = models.ForeignKey(OfertaCarona, on_delete=models.PROTECT, related_name='reservas')
    passageiro = models.ForeignKey(Usuario, on_delete=models.PROTECT, related_name='reservas')
    data_reserva = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=[('pendente', 'Pendente'), ('confirmada', 'Confirmada'), ('cancelada', 'Cancelada')],
        default='pendente'
    )

    class Meta:
        unique_together = ('oferta', 'passageiro')

    def __str__(self):
        return f"Reserva de {self.passageiro.nome} em {self.oferta.origem} -> {self.oferta.destino}"
