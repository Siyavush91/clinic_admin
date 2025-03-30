import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import LabResult, LabOrder, Patient, Doctor

User = get_user_model()

class LabResultConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        if not self.user.is_authenticated:
            await self.close()
            return
        
        if self.user.role == 'patient':
            # Patients subscribe to their own lab results
            try:
                patient = await self.get_patient_profile(self.user.id)
                self.room_group_name = f'patient_lab_results_{patient.id}'
            except Patient.DoesNotExist:
                await self.close()
                return
        elif self.user.role == 'doctor':
            # Doctors subscribe to lab results for their patients
            try:
                doctor = await self.get_doctor_profile(self.user.id)
                self.room_group_name = f'doctor_lab_results_{doctor.id}'
            except Doctor.DoesNotExist:
                await self.close()
                return
        else:
            # Other roles not allowed
            await self.close()
            return
            
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        # Leave room group
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
    
    # Receive message from WebSocket
    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type')
            
            if message_type == 'subscribe_lab_order':
                lab_order_id = text_data_json.get('lab_order_id')
                if lab_order_id:
                    has_permission = await self.check_lab_order_permission(lab_order_id, self.user.id)
                    if has_permission:
                        await self.channel_layer.group_add(
                            f'lab_order_{lab_order_id}',
                            self.channel_name
                        )
        except json.JSONDecodeError:
            pass
    
    # Receive message from room group
    async def lab_result_notification(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps(event))
    
    @database_sync_to_async
    def get_patient_profile(self, user_id):
        return Patient.objects.get(user_id=user_id)
    
    @database_sync_to_async
    def get_doctor_profile(self, user_id):
        return Doctor.objects.get(user_id=user_id)
    
    @database_sync_to_async
    def check_lab_order_permission(self, lab_order_id, user_id):
        try:
            lab_order = LabOrder.objects.get(id=lab_order_id)
            if self.user.role == 'patient':
                return lab_order.patient.user_id == user_id
            elif self.user.role == 'doctor':
                return lab_order.doctor.user_id == user_id
            return False
        except LabOrder.DoesNotExist:
            return False 