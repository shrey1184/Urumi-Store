{{/*
Common labels for all resources
*/}}
{{- define "medusa.labels" -}}
app.kubernetes.io/name: {{ .Values.storeName }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/part-of: store-platform
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "medusa.selectorLabels" -}}
app.kubernetes.io/name: {{ .Values.storeName }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Full host name
*/}}
{{- define "medusa.host" -}}
{{- if .Values.ingress.host -}}
{{ .Values.ingress.host }}
{{- else -}}
{{ .Values.storeName }}.{{ .Values.baseDomain }}
{{- end -}}
{{- end }}
