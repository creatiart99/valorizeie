#!/usr/bin/env python3
"""Prepare the existing Valorize mirror for clean URLs and legal pages.

Run with Python 3. No third-party packages, network calls or credentials needed.
The original mirror is retained; _site is the generated deployment artifact.
"""
from pathlib import Path
from html import escape, unescape
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit, urlunsplit, unquote
import json
import hashlib
import re
import shutil

ROOT = Path(__file__).resolve().parent
OUT = ROOT / '_site'
ORIGIN = 'https://valorizeie.com'
EMAIL = 'valorizeie@gmail.com'

# Registered business information; update here whenever the company changes it.
LEGAL = {'updated': '2026-11-21',
 'responsible': {'display_name': 'VALORIZE I&E',
                 'legal_name': 'VALORIZE I&E S.A.S.',
                 'nit': '901.984.756-1',
                 'domicile': 'Bogotá D.C., Colombia',
                 'address': 'Calle 149 #54-29, Bogotá D.C., Colombia',
                 'email': 'valorizeie@gmail.com',
                 'phone': '+57 317 887 3523',
                 'whatsapp': 'https://wa.me/573178873523'},
 'needs_confirmation': ['Vigencia de los datos empresariales previamente registrados: razón social, NIT, '
                        'dirección y correo. No se detiene la implementación autorizada.',
                        'Asignación operativa de la persona o área que tramitará consultas y reclamos; se usa '
                        'contacto institucional sin inventar un cargo.'],
 'implementation_notes': ['No afirmar certificación o cumplimiento integral solo por publicar estos documentos.',
                          'La navegación no equivale a autorización general de datos. El banner de preferencias '
                          'no autoriza mensajes comerciales ni sustituye autorización cuando se requiera.',
                          'Ajustar el párrafo de Google Fonts si el sitio elimina esa dependencia.',
                          'La política de cookies supone eliminación de scripts WooCommerce heredados y ausencia '
                          'de analítica/publicidad, conforme auditoría técnica.'],
 'sources': [{'title': 'Ley 1581 de 2012, arts.4,8–12,14–16',
              'url': 'https://jurinfo.jep.gov.co/Normograma/compilacion/docs/ley_1581_2012.htm'},
             {'title': 'Decreto 1074 de 2015, capítulo25: autorización, conservación, políticas y derechos',
              'url': 'https://normograma.sena.edu.co/compilacion/docs/decreto_1074_2015_pr027.htm'},
             {'title': 'Autoridad de protección de datos personales', 'url': 'https://www.sic.gov.co/'}],
 'pages': [{'path': 'privacidad/',
            'title': 'Política de privacidad y tratamiento de datos',
            'description': 'Cómo VALORIZE I&E trata la información que compartes al consultar nuestros servicios '
                           'y ejercer tus derechos.',
            'intro': 'Esta política explica el tratamiento de los datos personales asociados al uso de '
                     'valorizeie.com y a las comunicaciones que recibimos sobre nuestros servicios de desarrollo '
                     'territorial y sostenibilidad financiera. Se basa en la Ley 1581 de 2012 y en su '
                     'reglamentación aplicable.',
            'sections': [{'title': 'Responsable y canales de atención',
                          'paragraphs': ['VALORIZE I&E S.A.S., NIT 901.984.756-1, con domicilio en Bogotá D.C., '
                                         'es responsable del tratamiento de la información que recibe mediante '
                                         'sus canales institucionales. Dirección: Calle 149 #54-29, Bogotá D.C., '
                                         'Colombia.',
                                         'Para consultas y reclamos sobre datos personales, escribe a '
                                         'valorizeie@gmail.com o contacta al +57 317 887 3523. Dirige tu mensaje '
                                         'a la atención institucional de protección de datos de VALORIZE I&E. El '
                                         'ejercicio de tus derechos es gratuito.'],
                          'include_responsible_details': True,
                          'links': [{'label': 'Escribir sobre protección de datos',
                                     'href': 'mailto:valorizeie@gmail.com?subject=Protecci%C3%B3n%20de%20datos%20personales%20-%20VALORIZE%20I%26E'},
                                    {'label': 'Ver canales de contacto', 'href': '/contacts/'},
                                    {'label': 'Ejercer derechos de hábeas data', 'href': '/habeas-data/'}]},
                         {'title': 'Qué información puede tratarse',
                          'items': ['Los datos que decidas comunicar al escribirnos o llamarnos: nombre, entidad '
                                    'o empresa, cargo, teléfono, correo y contenido de tu solicitud.',
                                    'La información sobre el proyecto que sea necesaria para entender tu '
                                    'consulta, preparar una propuesta o desarrollar una relación contractual.',
                                    'Los datos técnicos que el proveedor de alojamiento pueda registrar al servir '
                                    'las páginas, como dirección IP, fecha de acceso y datos básicos del '
                                    'navegador.',
                                    'Las preferencias de funcionamiento que se almacenan en tu propio navegador, '
                                    'según la política de cookies y almacenamiento local.'],
                          'paragraphs': ['El sitio es informativo y ofrece enlaces a canales externos de '
                                         'contacto. No tiene un formulario propio que reciba solicitudes en una '
                                         'base de datos de esta web ni una pasarela de pago. Evita enviar datos '
                                         'sensibles, datos de menores o información personal de terceros que no '
                                         'sea necesaria para tu solicitud.']},
                         {'title': 'Para qué se utilizan los datos',
                          'items': ['Responder consultas y solicitudes sobre nuestros servicios.',
                                    'Preparar propuestas y gestionar las etapas previas de una posible '
                                    'contratación.',
                                    'Cumplir las obligaciones de una relación contractual y las obligaciones '
                                    'legales que correspondan.',
                                    'Atender consultas y reclamos sobre datos personales, conservar la evidencia '
                                    'necesaria y gestionar la seguridad de los canales de atención.'],
                          'paragraphs': ['Una finalidad distinta, como enviarte publicidad o comunicaciones '
                                         'comerciales periódicas, requiere que se informe de forma específica y '
                                         'se obtenga la autorización que corresponda. Contactarnos o seguir '
                                         'navegando no implica aceptar todas las finalidades posibles.']},
                         {'title': 'Autorización y datos especiales',
                          'paragraphs': ['Cuando el tratamiento requiera autorización, deberá solicitarse de '
                                         'forma previa e informada y conservarse una prueba que pueda '
                                         'consultarse. Las excepciones legales no eliminan los deberes de '
                                         'protección de datos.',
                                         'No estás obligado a suministrar datos sensibles. Este sitio no está '
                                         'dirigido a recolectar información de niños, niñas o adolescentes. Si '
                                         'una actuación requiere información especial, su tratamiento deberá '
                                         'cumplir los requisitos específicos aplicables.']},
                         {'title': 'Proveedores y enlaces externos',
                          'paragraphs': ['Las páginas se alojan mediante GitHub Pages. El proveedor de '
                                         'infraestructura puede procesar datos técnicos necesarios para operar y '
                                         'proteger su servicio. La información se encuentra sujeta también a las '
                                         'políticas del proveedor en lo que le corresponde.',
                                         'Los enlaces a WhatsApp, al correo o al teléfono abren servicios o '
                                         'aplicaciones de terceros cuando decides utilizarlos. Esos proveedores '
                                         'pueden aplicar sus propias condiciones y políticas; el contenido que '
                                         'envíes por dichos canales no se almacena dentro de esta página '
                                         'estática.',
                                         'La web puede solicitar fuentes tipográficas a Google Fonts. Esa '
                                         'conexión permite al proveedor recibir los datos técnicos de la '
                                         'solicitud, incluida la dirección IP. No se utiliza en este sitio como '
                                         'una herramienta de analítica o publicidad.',
                                         'Cualquier encargado que trate datos por cuenta de VALORIZE I&E debe '
                                         'actuar dentro de las finalidades autorizadas y con las obligaciones '
                                         'legales y contractuales aplicables. Las transmisiones o transferencias '
                                         'internacionales que lleguen a realizarse deben observar los requisitos '
                                         'de la normativa colombiana.'],
                          'links': [{'label': 'Privacidad de GitHub',
                                     'href': 'https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement'},
                                    {'label': 'Privacidad de WhatsApp',
                                     'href': 'https://www.whatsapp.com/legal/privacy-policy'},
                                    {'label': 'Privacidad de Google',
                                     'href': 'https://policies.google.com/privacy'}]},
                         {'title': 'Conservación, acceso y seguridad',
                          'paragraphs': ['Los datos deben conservarse durante el tiempo razonable y necesario '
                                         'para la finalidad informada y para atender las obligaciones legales o '
                                         'contractuales que correspondan. Una vez agotados esos motivos, deberán '
                                         'suprimirse o anonimizarse de forma adecuada. No se establece aquí un '
                                         'plazo único para todos los datos y relaciones.',
                                         'El acceso a la información debe limitarse a las personas autorizadas y '
                                         'a quienes puedan recibirla conforme a la ley. Su manejo debe respetar '
                                         'los principios de finalidad, calidad, seguridad y confidencialidad. No '
                                         'envíes contraseñas, códigos de autenticación ni datos de tarjetas por '
                                         'estos canales.']},
                         {'title': 'Tus derechos y vigencia',
                          'paragraphs': ['Puedes solicitar acceso gratuito, conocer el uso de tus datos, '
                                         'actualizarlos o rectificarlos, pedir prueba de la autorización y '
                                         'solicitar su revocatoria o la supresión de la información cuando '
                                         'proceda. También puedes acudir a la Superintendencia de Industria y '
                                         'Comercio después de agotar el trámite correspondiente ante el '
                                         'responsable o encargado.',
                                         'Consulta el procedimiento y los términos de respuesta en la página de '
                                         'hábeas data. Esta versión se publica el 21 de noviembre de 2026. Los '
                                         'cambios sustanciales deberán comunicarse oportunamente antes de '
                                         'implementarse, y las finalidades nuevas que lo requieran deberán contar '
                                         'con la autorización correspondiente.'],
                          'links': [{'label': 'Procedimiento de hábeas data', 'href': '/habeas-data/'},
                                    {'label': 'Cookies y almacenamiento local',
                                     'href': '/politica-de-cookies/'}]}]},
           {'path': 'habeas-data/',
            'title': 'Hábeas data: consultas y reclamos',
            'description': 'Conoce cómo solicitar acceso, actualización, corrección, supresión o revocatoria '
                           'sobre tus datos personales.',
            'intro': 'Puedes ejercer gratuitamente tus derechos sobre los datos personales tratados por VALORIZE '
                     'I&E. No necesitas contratar un abogado para presentar una consulta o un reclamo por '
                     'nuestros canales de atención.',
            'sections': [{'title': 'Qué puedes solicitar',
                          'items': ['Conocer y consultar tus datos personales y el uso que se les ha dado.',
                                    'Actualizar información o corregir datos inexactos, incompletos o '
                                    'desactualizados.',
                                    'Solicitar prueba de la autorización cuando sea exigible.',
                                    'Pedir la supresión de datos o revocar la autorización cuando proceda.',
                                    'Presentar un reclamo si consideras que el tratamiento desconoce tus '
                                    'derechos.'],
                          'paragraphs': ['La supresión y la revocatoria pueden estar limitadas cuando exista una '
                                         'obligación legal o contractual de conservar la información. En ese '
                                         'caso, la respuesta debe explicar el fundamento aplicable.']},
                         {'title': 'Cómo presentar tu solicitud',
                          'paragraphs': ['Envía tu consulta o reclamo a valorizeie@gmail.com con el asunto '
                                         '«Hábeas data — VALORIZE I&E». También puedes iniciar el trámite por '
                                         'WhatsApp en el número +57 317 887 3523, o mediante comunicación '
                                         'dirigida a Calle 149 #54-29, Bogotá D.C., Colombia. Conserva una copia '
                                         'de la solicitud y de su fecha de envío.'],
                          'items': ['Indica tu nombre y los datos necesarios para identificarte y verificar que '
                                    'eres el titular o su representante autorizado.',
                                    'Describe de forma clara qué información consultas o qué corrección, '
                                    'actualización, supresión o revocatoria solicitas.',
                                    'Incluye un medio para recibir la respuesta y, para un reclamo, los hechos y '
                                    'documentos que quieras aportar.',
                                    'Si actúas por otra persona, acredita la representación por el medio que '
                                    'corresponda.'],
                          'paragraphs_after': ['La verificación de identidad debe ser proporcional al trámite. No '
                                               'envíes información sensible ni copias completas de documentos si '
                                               'no son necesarias; utiliza el canal que el responsable indique '
                                               'para una verificación segura.'],
                          'links': [{'label': 'Enviar solicitud por correo',
                                     'href': 'mailto:valorizeie@gmail.com?subject=H%C3%A1beas%20data%20-%20VALORIZE%20I%26E'},
                                    {'label': 'Abrir WhatsApp para una solicitud de hábeas data',
                                     'href': 'https://wa.me/573178873523?text=Hola%2C%20quiero%20presentar%20una%20solicitud%20de%20h%C3%A1beas%20data%20ante%20VALORIZE%20I%26E.'},
                                    {'label': 'Otros canales de contacto', 'href': '/contacts/'}]},
                         {'title': 'Términos de respuesta',
                          'table': {'headers': ['Trámite', 'Plazo legal', 'Prórroga excepcional'],
                                    'rows': [['Consulta de información',
                                              'Hasta 10 días hábiles desde su recepción.',
                                              'Hasta 5 días hábiles adicionales, informando el motivo de la '
                                              'demora y la fecha de respuesta.'],
                                             ['Reclamo',
                                              'Hasta 15 días hábiles desde el día siguiente a su recepción.',
                                              'Hasta 8 días hábiles adicionales, informando el motivo de la '
                                              'demora y la fecha de respuesta.']]},
                          'paragraphs': ['Estos términos corresponden a los artículos 14 y 15 de la Ley 1581 de '
                                         '2012. Se aplicarán los términos inferiores que una norma especial '
                                         'establezca cuando corresponda.']},
                         {'title': 'Si un reclamo está incompleto',
                          'paragraphs': ['Se solicitará la información que falte dentro de los cinco días '
                                         'siguientes a su recepción. Si transcurren dos meses desde ese '
                                         'requerimiento sin que se complete, se entenderá desistido el reclamo.',
                                         'Cuando se reciba el reclamo completo, deberá incluirse la anotación de '
                                         'reclamo en trámite y su motivo en la base de datos correspondiente en '
                                         'un máximo de dos días hábiles, hasta que se decida. Si el receptor no '
                                         'es competente, deberá trasladarlo a quien corresponda en un máximo de '
                                         'dos días hábiles e informar al solicitante.']},
                         {'title': 'Acudir a la autoridad',
                          'paragraphs': ['Si consideras que tu consulta o reclamo no fue resuelto conforme a la '
                                         'ley, puedes acudir a la Superintendencia de Industria y Comercio una '
                                         'vez agotado el trámite ante el responsable o encargado. Conserva la '
                                         'solicitud, la respuesta recibida y los soportes pertinentes.'],
                          'links': [{'label': 'Superintendencia de Industria y Comercio',
                                     'href': 'https://www.sic.gov.co/'}]},
                         {'title': 'Información relacionada',
                          'paragraphs': ['Este procedimiento se complementa con nuestra política de privacidad y '
                                         'tratamiento de datos. Versión del 21 de noviembre de 2026.'],
                          'links': [{'label': 'Política de privacidad y tratamiento de datos',
                                     'href': '/privacidad/'}]}]},
           {'path': 'politica-de-cookies/',
            'title': 'Cookies y almacenamiento local',
            'description': 'Qué se guarda en tu navegador y cómo administrar tus preferencias en la web de '
                           'VALORIZE I&E.',
            'intro': 'Esta página explica el uso de cookies y tecnologías de almacenamiento del navegador en '
                     'valorizeie.com. Una cookie y el almacenamiento local son mecanismos distintos, aunque ambos '
                     'pueden conservar información en tu dispositivo.',
            'sections': [{'title': 'Qué utiliza esta web',
                          'paragraphs': ['La versión actual utiliza almacenamiento funcional del navegador para '
                                         'recordar preferencias de la interfaz y tu elección en el aviso de '
                                         'almacenamiento. Los componentes de presentación pueden usar '
                                         'almacenamiento local o de sesión para su funcionamiento.',
                                         'No se ha configurado Google Analytics, Meta Pixel ni otras herramientas '
                                         'de publicidad o medición de audiencia en esta versión. No hay '
                                         'categorías opcionales de analítica o publicidad activas que debas '
                                         'aceptar para consultar el contenido.'],
                          'table': {'headers': ['Uso', 'Finalidad', 'Conservación'],
                                    'rows': [['Preferencia del aviso',
                                              'Recordar tu elección en este navegador y dispositivo.',
                                              'Durante 180 días desde la elección, o hasta que la cambies o '
                                              'borres los datos del sitio.'],
                                             ['Almacenamiento funcional de la interfaz',
                                              'Permitir el funcionamiento de componentes y sus preferencias.',
                                              'Durante la sesión o mientras el componente necesite la '
                                              'preferencia, según su mecanismo de almacenamiento.']]}},
                         {'title': 'Cómo administrar tu elección',
                          'paragraphs': ['Puedes abrir las preferencias desde el enlace de cookies del pie de '
                                         'página. También puedes borrar o bloquear las cookies y el '
                                         'almacenamiento de valorizeie.com desde la configuración de tu '
                                         'navegador.',
                                         'La elección se aplica al navegador y dispositivo donde la guardas. Si '
                                         'usas otro dispositivo, navegación privada o eliminas los datos del '
                                         'sitio, el aviso puede volver a aparecer. Rechazar categorías opcionales '
                                         'no impide consultar la información de la web.',
                                         'El aviso no autoriza por sí mismo el envío de publicidad, el '
                                         'tratamiento de datos sensibles ni usos diferentes a los descritos. Si '
                                         'se incorporan herramientas opcionales en el futuro, deberán informarse '
                                         'y activarse solo cuando corresponda según la elección del visitante.']},
                         {'title': 'Conexiones con terceros',
                          'paragraphs': ['El sitio se sirve desde GitHub Pages y puede cargar fuentes de Google '
                                         'Fonts. La descarga de una fuente o de un archivo implica una solicitud '
                                         'técnica al proveedor, aunque no sea una cookie de publicidad.',
                                         'WhatsApp y otras aplicaciones enlazadas se abren cuando eliges usarlas. '
                                         'Sus propios sitios o aplicaciones pueden utilizar tecnologías sujetas a '
                                         'sus políticas. Esta página no controla el almacenamiento que esos '
                                         'servicios utilicen fuera de valorizeie.com.'],
                          'links': [{'label': 'Privacidad de GitHub',
                                     'href': 'https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement'},
                                    {'label': 'Privacidad de Google',
                                     'href': 'https://policies.google.com/privacy'},
                                    {'label': 'Privacidad de WhatsApp',
                                     'href': 'https://www.whatsapp.com/legal/privacy-policy'}]},
                         {'title': 'Contacto y actualizaciones',
                          'paragraphs': ['Para preguntas sobre datos personales, utiliza los canales '
                                         'institucionales de VALORIZE I&E o el procedimiento de hábeas data. Esta '
                                         'política describe la configuración publicada el 21 de noviembre de 2026 '
                                         'y deberá actualizarse si cambian las tecnologías o sus finalidades.'],
                          'links': [{'label': 'Contactar a VALORIZE I&E', 'href': '/contacts/'},
                                    {'label': 'Hábeas data', 'href': '/habeas-data/'}]}]},
           {'path': 'terminos-de-uso/',
            'title': 'Aviso legal y términos de uso',
            'description': 'Condiciones de consulta del sitio informativo de VALORIZE I&E, sus contenidos y '
                           'canales de contacto.',
            'intro': 'valorizeie.com presenta información institucional y servicios de consultoría en desarrollo '
                     'territorial, captura del valor del suelo, planeación y finanzas públicas. Estos términos se '
                     'refieren al uso de la web; los servicios profesionales se acuerdan de manera independiente.',
            'sections': [{'title': 'Titular y contacto',
                          'paragraphs': ['El titular de esta web es VALORIZE I&E S.A.S., NIT 901.984.756-1, con '
                                         'domicilio en Bogotá D.C., Colombia. Dirección: Calle 149 #54-29. Correo '
                                         'institucional: valorizeie@gmail.com. Teléfono: +57 317 887 3523.',
                                         'Las consultas sobre el contenido o estos términos pueden dirigirse a '
                                         'estos canales o a la página de contacto.'],
                          'include_responsible_details': True,
                          'links': [{'label': 'Información de contacto', 'href': '/contacts/'}]},
                         {'title': 'Alcance de la información',
                          'paragraphs': ['Los textos, ejemplos y descripciones ofrecen información general sobre '
                                         'la firma y sus áreas de servicio. Su consulta no sustituye el análisis '
                                         'técnico, jurídico, económico o financiero de un caso concreto.',
                                         'Una visita, una conversación inicial o una solicitud de información no '
                                         'constituyen por sí mismas un contrato ni una oferta irrevocable. El '
                                         'alcance, honorarios, plazos, entregables y responsabilidades de un '
                                         'servicio se definirán en la propuesta y el contrato que las partes '
                                         'acuerden.',
                                         'Esta web no realiza ventas con carrito, pagos en línea ni contratación '
                                         'automática. No solicita datos de tarjetas o claves bancarias.']},
                         {'title': 'Uso adecuado y propiedad intelectual',
                          'paragraphs': ['Utiliza el sitio de forma lícita y respetuosa. No intentes acceder sin '
                                         'autorización a sistemas, interferir con su funcionamiento, introducir '
                                         'contenido malicioso o utilizar la identidad de la firma para engañar a '
                                         'otras personas.',
                                         'Los textos, diseños y materiales están protegidos por los derechos que '
                                         'correspondan a sus titulares. La consulta pública no transfiere '
                                         'licencias de explotación sobre ellos. Para reutilizaciones que '
                                         'requieran autorización, contacta a la firma, sin perjuicio de los usos '
                                         'permitidos por la ley.',
                                         'Las marcas, logotipos y referencias de terceros conservan sus '
                                         'respectivos titulares. Su aparición como referencia de experiencia o '
                                         'colaboración no permite atribuirles avales o relaciones diferentes a '
                                         'las expresamente descritas.']},
                         {'title': 'Disponibilidad, enlaces y correcciones',
                          'paragraphs': ['La web puede actualizarse, interrumpirse por mantenimiento o presentar '
                                         'errores. Si detectas información incorrecta o un enlace que no '
                                         'funciona, puedes comunicarlo para su revisión.',
                                         'Los enlaces externos se facilitan para contacto o consulta. El '
                                         'contenido y funcionamiento de esos servicios dependen de sus propios '
                                         'responsables. Cualquier limitación de responsabilidad se entiende '
                                         'dentro de los límites de la legislación aplicable y no elimina derechos '
                                         'irrenunciables.']},
                         {'title': 'Privacidad y canales de derechos',
                          'paragraphs': ['El tratamiento de datos personales se explica en la política de '
                                         'privacidad. La página de hábeas data describe cómo presentar consultas '
                                         'y reclamos. Las tecnologías de almacenamiento se describen en la '
                                         'política de cookies.'],
                          'links': [{'label': 'Privacidad y tratamiento de datos', 'href': '/privacidad/'},
                                    {'label': 'Hábeas data', 'href': '/habeas-data/'},
                                    {'label': 'Cookies y almacenamiento local', 'href': '/politica-de-cookies/'}]},
                         {'title': 'Normativa aplicable y cambios',
                          'paragraphs': ['El uso de este sitio se interpreta conforme a las normas aplicables en '
                                         'Colombia. Los derechos y mecanismos de protección que resulten '
                                         'obligatorios se mantienen vigentes.',
                                         'Esta versión se publica el 21 de noviembre de 2026. Los cambios se '
                                         'reflejarán en esta página. Los acuerdos de servicios que ya se hayan '
                                         'celebrado se rigen por sus propios términos y no se modifican '
                                         'automáticamente por una actualización de la web.']}]}],
 'business_details_source': 'Datos empresariales previamente registrados en la conversación; vigencia no '
                            'reconfirmada.'}

LEGAL_CSS = r'''
:root{--vl-ink:#132d43;--vl-green:#457120;--vl-soft:#f4f7f3;--vl-line:#d8e0e5}
.vz-legal-footer{padding:28px max(24px,calc((100% - 1280px)/2));background:#102637;color:#fff;font:400 15px/1.7 Manrope,Arial,sans-serif;position:relative;z-index:2}
.vz-legal-footer nav{display:flex;flex-wrap:wrap;gap:12px 28px;align-items:center}.vz-legal-footer a,.vz-legal-footer button{color:#fff!important;font:inherit;text-decoration:underline;text-underline-offset:4px;background:none;border:0;padding:0;cursor:pointer}.vz-legal-footer p{font-size:14px;color:#c4d0d7;margin:16px 0 0}
.vz-legal-footer a:focus-visible,.vz-legal-footer button:focus-visible,.vz-cookie button:focus-visible,.vz-cookie a:focus-visible{outline:3px solid #91c65b;outline-offset:5px}
.vz-cookie{position:fixed;z-index:2147483640;left:24px;bottom:24px;width:min(570px,calc(100vw - 48px));box-sizing:border-box;background:#fff;color:var(--vl-ink);border:1px solid var(--vl-line);border-radius:18px;padding:24px;box-shadow:0 16px 64px #071a3840;font:400 16px/1.55 Manrope,Arial,sans-serif}
.vz-cookie[hidden]{display:none!important}.vz-cookie h2{font:700 21px/1.25 Manrope,Arial,sans-serif;color:var(--vl-ink);margin:0 0 12px}.vz-cookie p{font:inherit;margin:0 0 18px;color:#435460}.vz-cookie a{color:var(--vl-ink);text-decoration:underline;text-underline-offset:3px}.vz-cookie-actions{display:flex;gap:10px;flex-wrap:wrap}.vz-cookie button{appearance:none;border:1px solid var(--vl-green);border-radius:9px;padding:11px 17px;font:700 15px/1.35 Manrope,Arial,sans-serif;cursor:pointer;min-height:44px;white-space:normal}.vz-cookie-accept{background:var(--vl-green);color:#fff}.vz-cookie-reject{background:#fff;color:var(--vl-green)}.vz-cookie-status{font:400 14px/1.5 Manrope,Arial,sans-serif;color:#52616e;margin-top:12px;display:block}.vz-cookie-visible .vz-whatsapp{bottom:calc(var(--vz-cookie-height,240px) + 24px)}
.vl-page{margin:0;background:#f6f8f7;color:var(--vl-ink);font:400 17px/1.75 Manrope,Arial,sans-serif}.vl-page *{box-sizing:border-box}.vl-page a{color:#345d1c;text-underline-offset:4px}.vl-header{background:#fff;border-bottom:1px solid var(--vl-line);padding:24px max(24px,calc((100% - 1180px)/2));display:flex;gap:24px;justify-content:space-between;align-items:center}.vl-brand{font-size:23px;font-weight:800;letter-spacing:-.03em;color:var(--vl-ink)!important;text-decoration:none}.vl-header nav{display:flex;flex-wrap:wrap;gap:22px;font-size:15px}.vl-header nav a{color:var(--vl-ink)}.vl-main{max-width:1180px;margin:auto;padding:64px 24px 88px}.vl-kicker{font-size:14px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:var(--vl-green)}.vl-page h1{max-width:960px;font-size:clamp(36px,5vw,58px);line-height:1.08;letter-spacing:-.04em;margin:14px 0 24px}.vl-intro{max-width:900px;font-size:20px;color:#4b5b67}.vl-updated{font-size:14px;color:#576975;margin:24px 0 38px}.vl-layout{display:grid;grid-template-columns:220px minmax(0,1fr);gap:42px;align-items:start}.vl-toc{position:sticky;top:24px;background:#fff;border:1px solid var(--vl-line);border-radius:14px;padding:22px;font-size:14px}.vl-toc strong{display:block;margin-bottom:12px}.vl-toc a{display:block;color:var(--vl-ink);margin:10px 0}.vl-content{background:#fff;border:1px solid var(--vl-line);border-radius:18px;padding:38px;min-width:0}.vl-content section{scroll-margin-top:24px}.vl-content h2{font-size:25px;line-height:1.3;margin:0 0 18px;color:var(--vl-ink)}.vl-content section+section{border-top:1px solid var(--vl-line);margin-top:32px;padding-top:32px}.vl-content p{margin:0 0 18px}.vl-content ul{padding-left:24px;margin:0 0 20px}.vl-content li+li{margin-top:10px}.vl-links{display:flex;flex-wrap:wrap;gap:12px 22px;margin-top:18px}.vl-table-wrap{overflow:auto}.vl-content table{width:100%;border-collapse:collapse;font-size:15px;margin:20px 0}.vl-content th,.vl-content td{text-align:left;vertical-align:top;border:1px solid var(--vl-line);padding:13px;min-width:150px}.vl-content th{background:var(--vl-soft)}.vl-source-note{margin-top:30px;font-size:14px;color:#576975}.vl-error{max-width:780px;margin:auto;padding:100px 24px}.vl-error nav{display:flex;gap:24px;flex-wrap:wrap}
@media(max-width:800px){.vl-header{align-items:flex-start;flex-direction:column}.vl-header nav{gap:14px 20px}.vl-main{padding-top:42px}.vl-layout{grid-template-columns:1fr;gap:24px}.vl-toc{position:static}.vl-content{padding:25px 20px}.vz-cookie{left:14px;bottom:14px;width:calc(100vw - 28px);padding:20px}.vz-cookie-actions{display:grid;grid-template-columns:1fr 1fr}.vz-cookie button{padding:11px}.vz-legal-footer nav{gap:12px 22px}.vz-cookie-visible .vz-whatsapp{bottom:calc(var(--vz-cookie-height,280px) + 24px)}}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto!important}}
.vz-menu-toggle{border:0!important;cursor:pointer;display:inline-flex;align-items:center;justify-content:center;background:#fff!important;color:#132d43!important;border-radius:50%}
.vz-mobile-nav{border:1px solid var(--vl-line);border-radius:18px;padding:26px;width:min(420px,calc(100vw - 32px));max-height:calc(100dvh - 32px);box-sizing:border-box;overflow:auto;background:#fff;color:var(--vl-ink);font:400 18px/1.5 Manrope,Arial,sans-serif}.vz-mobile-nav::backdrop{background:#071a38b3}.vz-mobile-nav header{display:flex;align-items:center;justify-content:space-between;gap:16px;margin-bottom:18px}.vz-mobile-nav h2{font:700 23px/1.3 Manrope,Arial,sans-serif;margin:0;color:var(--vl-ink)}.vz-mobile-nav button{border:1px solid var(--vl-line);border-radius:8px;background:#fff;color:var(--vl-ink);font:600 15px/1.3 Manrope,Arial,sans-serif;min-height:44px;padding:10px 14px;cursor:pointer}.vz-mobile-nav nav{display:grid;gap:8px}.vz-mobile-nav nav a{color:var(--vl-ink);background:#f4f7f3;border-radius:8px;padding:13px 16px;text-decoration:none;font:600 18px/1.5 Manrope,Arial,sans-serif}.vz-mobile-nav a:focus-visible,.vz-mobile-nav button:focus-visible,.vz-menu-toggle:focus-visible{outline:3px solid #457120;outline-offset:3px}
.vz-faq-answer[hidden]{display:none!important}.vz-faq-answer:not([hidden]){display:block!important}
.elementor-widget-cmsmasters-blog-slider .swiper{overflow-x:auto!important;overflow-y:hidden!important;scroll-snap-type:x mandatory}.elementor-widget-cmsmasters-blog-slider .swiper-wrapper{display:flex!important;gap:30px;transform:none!important;transition:none!important;height:auto!important;align-items:stretch}.elementor-widget-cmsmasters-blog-slider .swiper-slide{flex:0 0 calc((100% - 60px)/3);width:calc((100% - 60px)/3)!important;height:auto;scroll-snap-align:start}
@media(max-width:1180px){.elementor-widget-cmsmasters-blog-slider .swiper-slide{flex-basis:calc((100% - 30px)/2);width:calc((100% - 30px)/2)!important}}
@media(max-width:767px){.elementor-widget-cmsmasters-blog-slider .swiper-slide{flex-basis:100%;width:100%!important}}
'''

CLEAN_JS = r'''
(function(){
  if (/\/index\.html$/i.test(location.pathname)) {
    history.replaceState(history.state, '', location.pathname.replace(/index\.html$/i, '') + location.search + location.hash);
  }
})();
'''

CONSENT_JS = r'''
(function(){
  'use strict';
  var KEY='vz_privacy_preferences', VERSION='2026-11-21', DAYS=180;
  var previousFocus=null, panel=null;
  function read(){try{var p=JSON.parse(localStorage.getItem(KEY));if(p&&p.version===VERSION&&Date.now()<p.expiresAt)return p;}catch(e){}return null;}
  function size(){if(panel&&!panel.hidden)document.documentElement.style.setProperty('--vz-cookie-height',panel.offsetHeight+'px');}
  function show(trigger){previousFocus=trigger||null;panel.hidden=false;document.body.classList.add('vz-cookie-visible');size();if(trigger)panel.querySelector('button').focus();}
  function save(optional){
    var now=Date.now(),p={version:VERSION,necessary:true,optional:optional,updatedAt:now,expiresAt:now+DAYS*86400000};
    try{localStorage.setItem(KEY,JSON.stringify(p));}catch(e){}
    panel.hidden=true;document.body.classList.remove('vz-cookie-visible');
    document.dispatchEvent(new CustomEvent('valorize:privacy-choice',{detail:p}));
    if(previousFocus&&document.contains(previousFocus))previousFocus.focus();
    document.querySelectorAll('[data-cookie-status]').forEach(function(e){e.textContent=optional?'Preferencia guardada: aceptar. No hay herramientas opcionales activas.':'Preferencia guardada: solo almacenamiento necesario.';});
  }
  function ready(){
    document.querySelectorAll('.elementor-widget-cmsmasters-toggles__title[aria-controls]').forEach(function(title){
      var answer=document.getElementById(title.getAttribute('aria-controls'));if(!answer)return;
      title.setAttribute('role','button');title.setAttribute('tabindex','0');answer.classList.add('vz-faq-answer');answer.hidden=title.getAttribute('aria-expanded')!=='true';
      title.addEventListener('click',function(e){e.preventDefault();var open=title.getAttribute('aria-expanded')==='true';title.setAttribute('aria-expanded',String(!open));title.classList.toggle('elementor-active',!open);answer.hidden=open;});
      title.addEventListener('keydown',function(e){if(e.key==='Enter'||e.key===' '){e.preventDefault();title.click();}});
    });
    document.querySelectorAll('.elementor-widget-cmsmasters-blog-slider .swiper').forEach(function(slider){slider.setAttribute('tabindex','0');slider.setAttribute('role','region');slider.setAttribute('aria-label','Galería de equipo y servicios; desplázate para ver más');});
    var menu=document.querySelector('#vz-mobile-nav');
    var menuButtons=document.querySelectorAll('.vz-menu-toggle');
    if(menu&&menuButtons.length){
      var menuTrigger=null;
      menuButtons.forEach(function(b){b.addEventListener('click',function(){menuTrigger=b;b.setAttribute('aria-expanded','true');menu.showModal();});});
      menu.querySelector('[data-menu-close]').addEventListener('click',function(){menu.close();});
      menu.addEventListener('close',function(){menuButtons.forEach(function(b){b.setAttribute('aria-expanded','false');});if(menuTrigger)menuTrigger.focus();});
    }
    panel=document.createElement('section');panel.className='vz-cookie';panel.hidden=true;
    panel.setAttribute('role','region');panel.setAttribute('aria-labelledby','vz-cookie-title');
    panel.innerHTML='<h2 id="vz-cookie-title">Tu privacidad y tus preferencias</h2><p>Usamos almacenamiento funcional para que la web opere y recordar tu elección. No tenemos analítica ni publicidad activa. Guardamos tu elección durante 180 días. Consulta nuestra <a href="/politica-de-cookies/">política de cookies y almacenamiento local</a>.</p><div class="vz-cookie-actions"><button type="button" class="vz-cookie-accept">Aceptar</button><button type="button" class="vz-cookie-reject">Solo necesarias</button></div>';
    document.body.appendChild(panel);
    panel.querySelector('.vz-cookie-accept').addEventListener('click',function(){save(true);});
    panel.querySelector('.vz-cookie-reject').addEventListener('click',function(){save(false);});
    document.querySelectorAll('[data-cookie-settings]').forEach(function(b){b.addEventListener('click',function(){show(b);});});
    window.addEventListener('resize',size);
    window.addEventListener('storage',function(e){if(e.key===KEY&&read()){panel.hidden=true;document.body.classList.remove('vz-cookie-visible');}});
    if(!read())show(null);
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',ready);else ready();
})();
'''

FOOTER = '''<footer class="vz-legal-footer"><nav aria-label="Información legal"><a href="/privacidad/">Privacidad y datos personales</a><a href="/habeas-data/">Hábeas data</a><a href="/politica-de-cookies/">Política de cookies</a><a href="/terminos-de-uso/">Aviso legal y términos de uso</a><button type="button" data-cookie-settings>Preferencias de cookies</button></nav><p>VALORIZE I&amp;E S.A.S. · <a href="mailto:valorizeie@gmail.com">valorizeie@gmail.com</a> · <a href="tel:+573178873523">+57 317 887 3523</a></p></footer>'''
ASSET_VERSION = hashlib.sha256((LEGAL_CSS+CLEAN_JS+CONSENT_JS).encode()).hexdigest()[:12]
HEAD_EXTRA = '<script src="/assets/url-cleanup.js?v='+ASSET_VERSION+'"></script><link rel="stylesheet" href="/assets/site-legal.css?v='+ASSET_VERSION+'">'
MOBILE_NAV = '<dialog id="vz-mobile-nav" class="vz-mobile-nav" aria-labelledby="vz-menu-title"><header><h2 id="vz-menu-title">Menú</h2><button type="button" data-menu-close>Cerrar menú</button></header><nav aria-label="Navegación móvil"><a href="/">Inicio</a><a href="/our-services/">Servicios</a><a href="/sobre-nosotros/">Nosotros</a><a href="/nuestro-equipo/">Nuestro equipo</a><a href="/contacts/">Contacto</a></nav></dialog>'
BODY_EXTRA = FOOTER + MOBILE_NAV + '<script src="/assets/privacy-preferences.js?v='+ASSET_VERSION+'" defer></script>'

def page_path(path):
    relative=path.relative_to(OUT).as_posix()
    return '/' + relative.removesuffix('index.html')

def replace_href(match, path):
    quote,raw=match.group(1),match.group(2)
    value=unescape(raw)
    if 'cmsmasters-popup-' in value:
        value='/contacts/'
    elif 'cmsmasters-scroll-top' in value:
        value='#top'
    elif value.lower().startswith('https://valorize i'):
        value='/'
    elif value.lower().startswith('mailto:') and ('valorize i' in value.lower() or 'valorize%20i' in value.lower()):
        value='mailto:'+EMAIL
    elif value.lower().startswith('tel:'):
        value='tel:+573178873523'
    elif value and not value.startswith(('#','mailto:','tel:','javascript:')):
        parsed=urlsplit(urljoin(ORIGIN+page_path(path),value))
        if parsed.netloc in ('valorizeie.com','www.valorizeie.com'):
            candidate=parsed.path
            if candidate.endswith('index.html'):
                candidate=candidate[:-10]
            if not candidate:
                candidate='/'
            if candidate.endswith('/') or (OUT / unquote(candidate.lstrip('/'))).is_file():
                value=urlunsplit(('', '', candidate, parsed.query, parsed.fragment))
    return 'href='+quote+escape(value,quote=True)+quote

def clean_html(path):
    data=path.read_text(encoding='utf-8')
    data=data.replace('https://creatiart99.github.io/valorizeie/','https://valorizeie.com/')
    data=re.sub(r'<script\b[^>]*\bsrc=["\'][^"\']*/(?:woocommerce|sourcebuster|js-cookie)/[^"\']+["\'][^>]*>.*?</script>','',data,flags=re.I|re.S)
    data=re.sub(r'<script\b[^>]*\bid=["\']wc-order-attribution[^"\']*["\'][^>]*>.*?</script>','',data,flags=re.I|re.S)
    # Replace CMS runtime loaders whose asynchronous chunks were not mirrored.
    retired_scripts=r'(?:elementor-webpack-runtime-js|elementor-frontend-modules-js|elementor-frontend-js|elementor-pro-webpack-runtime-js|elementor-pro-frontend-js|pro-elements-handlers-js|cmsmasters-webpack-runtime-js|cmsmasters-frontend-js|cargo-trucking-frontend-js|forminator-[^"\']+)'
    data=re.sub(r'<script\b[^>]*\bid=["\']'+retired_scripts+r'["\'][^>]*>.*?</script>','',data,flags=re.I|re.S)
    # The mirrored CMS popup is unavailable; provide a real accessible mobile menu.
    data=re.sub(r'<a\b[^>]*>(\s*<i\b[^>]*\bcmsms-demo-icon-menu\b[^>]*></i>\s*)</a>',lambda m:'<button type="button" class="elementor-icon vz-menu-toggle" aria-label="Abrir menú" aria-controls="vz-mobile-nav" aria-expanded="false">'+m.group(1)+'</button>',data,flags=re.I|re.S)
    data=re.sub(r'href=(["\'])(.*?)\1',lambda m:replace_href(m,path),data,flags=re.I|re.S)
    data=re.sub(r'(?i)(?:contacto|Contacto)@(?:Valorize I&amp;E|Valorize I&E)',EMAIL,data)
    # A former payment redirect is unused; keep no legacy origin in inline configuration.
    data=data.replace('https:\\/\\/creatiart99.github.io\\/valorizeie\\/','https:\\/\\/valorizeie.com\\/')
    data=re.sub(r'(<link\b[^>]*\brel=["\']canonical["\'][^>]*href=["\'])[^"\']+',lambda m:m.group(1)+ORIGIN+page_path(path),data,flags=re.I)
    data=data.replace('</head>',HEAD_EXTRA+'</head>',1)
    data=re.sub(r'(<body\b[^>]*>)',r'\1<div id="top" tabindex="-1"></div>',data,count=1,flags=re.I)
    data=data.replace('</body>',BODY_EXTRA+'</body>',1)
    path.write_text(data,encoding='utf-8')

def render_section(section, index):
    body=''.join('<p>'+escape(p)+'</p>' for p in section.get('paragraphs',[]))
    if section.get('items'):
        body+='<ul>'+''.join('<li>'+escape(i)+'</li>' for i in section['items'])+'</ul>'
    body+=''.join('<p>'+escape(p)+'</p>' for p in section.get('paragraphs_after',[]))
    if section.get('table'):
        t=section['table']
        body+='<div class="vl-table-wrap"><table><thead><tr>'+''.join('<th scope="col">'+escape(h)+'</th>' for h in t['headers'])+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+escape(c)+'</td>' for c in row)+'</tr>' for row in t['rows'])+'</tbody></table></div>'
    if section.get('links'):
        body+='<div class="vl-links">'+''.join('<a href="'+escape(link['href'],quote=True)+'"'+(' rel="noopener noreferrer"' if link['href'].startswith('https://') else '')+'>'+escape(link['label'])+'</a>' for link in section['links'])+'</div>'
    return '<section id="seccion-'+str(index)+'"><h2>'+escape(section['title'])+'</h2>'+body+'</section>'

def render_legal(page):
    toc=''.join('<a href="#seccion-'+str(i)+'">'+escape(s['title'])+'</a>' for i,s in enumerate(page['sections'],1))
    sections=''.join(render_section(s,i) for i,s in enumerate(page['sections'],1))
    if page['path']=='politica-de-cookies/':
        sections+='<section id="preferencias"><h2>Preferencias en este navegador</h2><button type="button" class="vz-btn" data-cookie-settings>Gestionar preferencias de cookies</button><p data-cookie-status role="status"></p></section>'
    return '''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'''+escape(page['title'])+''' | VALORIZE I&amp;E</title><meta name="description" content="'''+escape(page['description'],quote=True)+'''"><link rel="canonical" href="'''+ORIGIN+'/'+page['path']+'''"><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;600;700;800&amp;display=swap">'''+HEAD_EXTRA+'''</head><body class="vl-page"><div id="top" tabindex="-1"></div><header class="vl-header"><a class="vl-brand" href="/">VALORIZE I&amp;E</a><nav aria-label="Navegación principal"><a href="/">Inicio</a><a href="/our-services/">Servicios</a><a href="/sobre-nosotros/">Nosotros</a><a href="/contacts/">Contacto</a></nav></header><main class="vl-main"><span class="vl-kicker">Información legal</span><h1>'''+escape(page['title'])+'''</h1><p class="vl-intro">'''+escape(page['intro'])+'''</p><p class="vl-updated">Última actualización: 21 de noviembre de 2026</p><div class="vl-layout"><aside class="vl-toc" aria-label="En esta página"><strong>En esta página</strong>'''+toc+'''</aside><article class="vl-content">'''+sections+'''</article></div></main>'''+BODY_EXTRA+'''</body></html>'''

class PageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True);self.refs=[];self.ids=set()
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if a.get('id'):self.ids.add(a['id'])
        for attribute in ('href','src','poster'):
            if a.get(attribute):self.refs.append((tag,attribute,a[attribute]))

def validate():
    documents={}
    for page in OUT.rglob('*.html'):
        parser=PageParser();parser.feed(page.read_text());documents[page]=parser
    failures=[];checked=0
    for page,parser in documents.items():
        for tag,attribute,value in parser.refs:
            if value.startswith(('mailto:','tel:','data:','javascript:')):continue
            parsed=urlsplit(urljoin(ORIGIN+page_path(page),value))
            if parsed.netloc not in ('valorizeie.com','www.valorizeie.com'):continue
            checked+=1
            target=OUT/unquote(parsed.path.lstrip('/'))
            if parsed.path.endswith('/'):target=target/'index.html'
            if not target.is_file():failures.append(f'{page.relative_to(OUT)}: missing {value}')
            elif parsed.fragment and target in documents and unquote(parsed.fragment) not in documents[target].ids:
                failures.append(f'{page.relative_to(OUT)}: missing anchor {value}')
            if tag=='a' and re.search(r'/index\.html(?:[?#]|$)',value):failures.append(f'{page}: unclean URL {value}')
    if failures:raise SystemExit('\n'.join(failures))
    print(f'Validated {len(documents)} HTML pages and {checked} internal links/resources.')

def main():
    if LEGAL is None:raise SystemExit('Policy content is missing.')
    if OUT.exists():shutil.rmtree(OUT)
    OUT.mkdir()
    for source in ROOT.iterdir():
        if source.name in ('_site','.git','.github','__pycache__','prepare_site.py','MIGRATION_REPORT.md'):continue
        if source.is_dir():shutil.copytree(source,OUT/source.name)
        elif source.suffix=='.html' or source.name in ('CNAME','.nojekyll'):shutil.copy2(source,OUT/source.name)
    for page in OUT.rglob('*.html'):clean_html(page)
    js_path=OUT/'assets/valorize-overrides.js'
    js=js_path.read_text()
    # Existing menu behavior must no longer reintroduce file names.
    js=js.replace('"index.html"','"/"').replace('"our-services/index.html"','"/our-services/"').replace('"sobre-nosotros/index.html"','"/sobre-nosotros/"').replace('"nuestro-equipo/index.html"','"/nuestro-equipo/"').replace('"contacts/index.html"','"/contacts/"')
    js=re.sub(r'"(services/[^"\n]+)/index\.html"',r'"/\1/"',js)
    js=js.replace('const local=p=>base+(routes[p]||"/");','const local=p=>routes[p]||"/";')
    js=re.sub(r'base\+"(/[^"\n]*)"',r'"\1"',js)
    js_path.write_text(js)
    (OUT/'assets/site-legal.css').write_text(LEGAL_CSS)
    (OUT/'assets/url-cleanup.js').write_text(CLEAN_JS)
    (OUT/'assets/privacy-preferences.js').write_text(CONSENT_JS)
    for page in LEGAL['pages']:
        dest=OUT/page['path']/'index.html';dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(render_legal(page))
    notfound='''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex"><title>Página no encontrada | VALORIZE I&amp;E</title>'''+HEAD_EXTRA+'''</head><body class="vl-page"><div id="top"></div><main class="vl-error"><p class="vl-kicker">Error 404</p><h1>Esta página no está disponible</h1><p>Puedes volver al inicio, explorar nuestros servicios o comunicarte con nosotros.</p><nav aria-label="Continuar navegando"><a href="/">Inicio</a><a href="/our-services/">Servicios</a><a href="/contacts/">Contacto</a></nav></main>'''+BODY_EXTRA+'''</body></html>'''
    (OUT/'404.html').write_text(notfound)
    pages=sorted(page_path(p) for p in OUT.rglob('index.html'))
    (OUT/'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join('<url><loc>'+ORIGIN+escape(p)+'</loc></url>' for p in pages)+'</urlset>')
    (OUT/'robots.txt').write_text('User-agent: *\nAllow: /\nSitemap: '+ORIGIN+'/sitemap.xml\n')
    validate()

if __name__=='__main__':main()
