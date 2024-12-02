{{- define "imagepullsecret.uname" -}}
{{- printf "imagepullsecret-%s" .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- end }}

{{- define "vkeServerlessTolerations" -}}

{{- end }}
# tolerations:
#   - key: "vci.vke.volcengine.com/node-type"
#     operator: "Equal"
#     value: "vci"
#     effect: "NoSchedule"



{{- define "client.uname" -}}
{{- printf "%s-%s" .Release.Name .Values.client.name | trunc 63 | trimSuffix "-" -}}
{{- end }}


{{- define "scheduler.uname" -}}
{{- printf "%s-%s" .Release.Name .Values.scheduler.name | trunc 63 | trimSuffix "-" -}}
{{- end }}


{{- define "scheduler.svc" -}}
{{- printf "%s-%s" .Release.Name .Values.scheduler.name | trunc 63 | trimSuffix "-" -}}:{{ .Values.scheduler.port }}
{{- end }}

{{- define "scheduler.selectorLabels" -}}
app.kubernetes.io/name: {{ required "scheduler.name is required" .Values.scheduler.name }}
app.kubernetes.io/service: {{ required "service is required" .Values.service }}
{{- end }}

{{- define "scheduler.labels" -}}
{{ include "scheduler.selectorLabels" . }}
{{- end }}

{{- define "worker.uname" -}}
{{- printf "%s-%s" .Release.Name .Values.worker.name | trunc 63 | trimSuffix "-" -}}
{{- end }}

{{- define "worker.selectorLabels" -}}
app.kubernetes.io/name: {{ required "worker.name is required" .Values.worker.name }}
app.kubernetes.io/service: {{ required "service is required" .Values.service }}
{{- end }}

{{- define "worker.labels" -}}
{{ include "worker.selectorLabels" . }}
{{- end }}
