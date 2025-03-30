import io
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from django.conf import settings
import os


def generate_medical_report(patient, diagnoses, prescriptions, lab_orders):
    """
    Generate a PDF medical report for a patient including diagnoses, prescriptions, and lab results
    """
    buffer = io.BytesIO()
    
    # Create the PDF object using ReportLab
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, 
                            topMargin=72, bottomMargin=72)
    
    # Container for PDF elements
    elements = []
    
    # Styles
    styles = getSampleStyleSheet()
    header_style = styles['Heading1']
    subheader_style = styles['Heading2']
    normal_style = styles['Normal']
    
    # Add clinic logo if available
    # logo_path = os.path.join(settings.STATIC_ROOT, 'images/clinic_logo.png')
    # if os.path.exists(logo_path):
    #     clinic_logo = Image(logo_path, width=200, height=50)
    #     elements.append(clinic_logo)
    #     elements.append(Spacer(1, 12))
    
    # Add report title
    elements.append(Paragraph("Medical Report", header_style))
    elements.append(Spacer(1, 12))
    
    # Add patient information
    elements.append(Paragraph("Patient Information", subheader_style))
    patient_info = [
        ["Name:", f"{patient.user.first_name} {patient.user.last_name}"],
        ["Date of Birth:", patient.date_of_birth.strftime("%Y-%m-%d")],
        ["Blood Group:", patient.blood_group or "Not specified"],
        ["Report Date:", datetime.now().strftime("%Y-%m-%d %H:%M")]
    ]
    
    patient_table = Table(patient_info, colWidths=[100, 300])
    patient_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.black),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(patient_table)
    elements.append(Spacer(1, 12))
    
    # Add diagnoses section
    if diagnoses:
        elements.append(Paragraph("Diagnoses", subheader_style))
        elements.append(Spacer(1, 6))
        
        diagnoses_data = [["Diagnosis", "Code", "Date", "Doctor"]]
        for diagnosis in diagnoses:
            diagnoses_data.append([
                diagnosis.diagnosis_name,
                diagnosis.diagnosis_code,
                diagnosis.diagnosis_date.strftime("%Y-%m-%d"),
                str(diagnosis.doctor)
            ])
        
        diagnoses_table = Table(diagnoses_data, colWidths=[180, 70, 80, 150])
        diagnoses_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        elements.append(diagnoses_table)
        elements.append(Spacer(1, 12))
    
    # Add prescriptions section
    if prescriptions:
        elements.append(Paragraph("Current Medications", subheader_style))
        elements.append(Spacer(1, 6))
        
        prescriptions_data = [["Medication", "Dosage", "Frequency", "Duration", "Start Date"]]
        for prescription in prescriptions:
            prescriptions_data.append([
                str(prescription.medication),
                prescription.dosage,
                prescription.frequency,
                prescription.duration,
                prescription.start_date.strftime("%Y-%m-%d")
            ])
        
        prescriptions_table = Table(prescriptions_data, colWidths=[100, 100, 100, 100, 80])
        prescriptions_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        elements.append(prescriptions_table)
        elements.append(Spacer(1, 12))
    
    # Add lab results section
    if lab_orders:
        elements.append(Paragraph("Laboratory Results", subheader_style))
        elements.append(Spacer(1, 6))
        
        for lab_order in lab_orders:
            elements.append(Paragraph(f"Order Date: {lab_order.order_date.strftime('%Y-%m-%d')}", 
                                     ParagraphStyle('LabOrderHeading', parent=normal_style, fontName='Helvetica-Bold')))
            elements.append(Spacer(1, 6))
            
            results = lab_order.results.all()
            if results:
                results_data = [["Test", "Result", "Normal Range", "Unit", "Abnormal"]]
                for result in results:
                    results_data.append([
                        result.lab_test.name,
                        result.value,
                        result.lab_test.normal_range or "",
                        result.lab_test.unit or "",
                        "Yes" if result.is_abnormal else "No"
                    ])
                
                results_table = Table(results_data, colWidths=[120, 100, 100, 60, 60])
                results_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('TEXTCOLOR', (4, 1), (4, -1), 
                                  lambda x, y: colors.red if x[4] == 'Yes' else colors.black),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ]))
                elements.append(results_table)
                elements.append(Spacer(1, 12))
            else:
                elements.append(Paragraph("No results available for this order", normal_style))
                elements.append(Spacer(1, 12))
    
    # Add footer
    elements.append(Spacer(1, 20))
    elements.append(Paragraph("This report is for medical purposes only.", 
                             ParagraphStyle('Footer', parent=normal_style, textColor=colors.gray, fontSize=8)))
    
    # Build the PDF
    doc.build(elements)
    
    # Get the value of the BytesIO buffer
    pdf = buffer.getvalue()
    buffer.close()
    
    return pdf


def generate_discharge_summary(hospitalization):
    """
    Generate a PDF discharge summary for a patient
    """
    buffer = io.BytesIO()
    
    # Create the PDF object using ReportLab
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, 
                            topMargin=72, bottomMargin=72)
    
    # Container for PDF elements
    elements = []
    
    # Styles
    styles = getSampleStyleSheet()
    header_style = styles['Heading1']
    subheader_style = styles['Heading2']
    normal_style = styles['Normal']
    
    # Add report title
    elements.append(Paragraph("Discharge Summary", header_style))
    elements.append(Spacer(1, 12))
    
    # Add patient information
    elements.append(Paragraph("Patient Information", subheader_style))
    patient = hospitalization.patient
    patient_info = [
        ["Name:", f"{patient.user.first_name} {patient.user.last_name}"],
        ["Date of Birth:", patient.date_of_birth.strftime("%Y-%m-%d")],
        ["Admission Date:", hospitalization.admission_date.strftime("%Y-%m-%d %H:%M")],
        ["Discharge Date:", hospitalization.discharge_date.strftime("%Y-%m-%d %H:%M") 
                            if hospitalization.discharge_date else "Not discharged"],
        ["Department:", str(hospitalization.department)],
        ["Attending Physician:", str(hospitalization.doctor)]
    ]
    
    patient_table = Table(patient_info, colWidths=[120, 280])
    patient_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.black),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(patient_table)
    elements.append(Spacer(1, 12))
    
    # Add reason for hospitalization
    elements.append(Paragraph("Reason for Hospitalization", subheader_style))
    elements.append(Paragraph(hospitalization.reason, normal_style))
    elements.append(Spacer(1, 12))
    
    # Add Discharge Summary
    if hospitalization.discharge_summary:
        elements.append(Paragraph("Discharge Summary", subheader_style))
        elements.append(Paragraph(hospitalization.discharge_summary, normal_style))
        elements.append(Spacer(1, 12))
    
    # Add footer
    elements.append(Spacer(1, 20))
    elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}", 
                             ParagraphStyle('Footer', parent=normal_style, textColor=colors.gray, fontSize=8)))
    
    # Build the PDF
    doc.build(elements)
    
    # Get the value of the BytesIO buffer
    pdf = buffer.getvalue()
    buffer.close()
    
    return pdf 