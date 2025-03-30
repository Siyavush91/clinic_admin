from django.db.models.signals import post_save
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json
from .models import LabResult, LabOrder

@receiver(post_save, sender=LabResult)
def notify_lab_result_update(sender, instance, created, **kwargs):
    """
    Signal to notify doctors and patients when lab results are created or updated
    """
    channel_layer = get_channel_layer()
    lab_order = instance.lab_order
    
    # Serialize the result data
    result_data = {
        'id': instance.id,
        'lab_test_name': instance.lab_test.name,
        'value': instance.value,
        'is_abnormal': instance.is_abnormal,
        'result_date': instance.result_date.isoformat(),
        'lab_order_id': lab_order.id,
        'patient_id': lab_order.patient.id,
        'doctor_id': lab_order.doctor.id,
        'unit': instance.lab_test.unit or ''
    }
    
    # Notify specific lab order subscribers
    async_to_sync(channel_layer.group_send)(
        f'lab_order_{lab_order.id}',
        {
            'type': 'lab_result_notification',
            'event': 'lab_result_update',
            'created': created,
            'result': result_data
        }
    )
    
    # Notify patient
    async_to_sync(channel_layer.group_send)(
        f'patient_lab_results_{lab_order.patient.id}',
        {
            'type': 'lab_result_notification',
            'event': 'lab_result_update',
            'created': created,
            'result': result_data
        }
    )
    
    # Notify doctor
    async_to_sync(channel_layer.group_send)(
        f'doctor_lab_results_{lab_order.doctor.id}',
        {
            'type': 'lab_result_notification',
            'event': 'lab_result_update',
            'created': created,
            'result': result_data
        }
    )
    
    # Update lab order status if needed
    if created:
        # Check if this is the first result
        if lab_order.status == 'ordered':
            lab_order.status = 'in_progress'
            lab_order.save(update_fields=['status'])
        
        # Check if all lab tests have results
        if lab_order.status == 'in_progress':
            # Get all related lab tests in this order
            results_count = lab_order.results.count()
            # Check if all tests in the order have been completed
            # This is a simplified example - in reality, you'd need to track 
            # which tests were ordered and which have results
            if results_count >= 3:  # Assuming at least 3 results is complete
                lab_order.status = 'completed'
                lab_order.save(update_fields=['status'])
                
                # Notify about completed lab order
                async_to_sync(channel_layer.group_send)(
                    f'patient_lab_results_{lab_order.patient.id}',
                    {
                        'type': 'lab_result_notification',
                        'event': 'lab_order_completed',
                        'lab_order_id': lab_order.id
                    }
                )
                
                async_to_sync(channel_layer.group_send)(
                    f'doctor_lab_results_{lab_order.doctor.id}',
                    {
                        'type': 'lab_result_notification',
                        'event': 'lab_order_completed',
                        'lab_order_id': lab_order.id
                    }
                ) 