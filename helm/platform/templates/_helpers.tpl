{{- define "platform.labels" -}}
app.kubernetes.io/name: store-platform
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}
