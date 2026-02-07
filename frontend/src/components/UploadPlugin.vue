<template>
  <input
    ref="fileInput"
    type="file"
    class="hidden"
    accept="image/*,video/*,audio/*,.pdf"
    @change="onPick"
  />
</template>

<script setup>
import { onMounted, ref, nextTick } from "vue"

const fileInput = ref(null)

const props = defineProps({
  onUploadStart: Function,
  onUploadProgress: Function,
  onUploadEnd: Function,
  onFileUploaded: { type: Function, required: true },
})

onMounted(async () => {
  await nextTick()
  fileInput.value?.click()
})

function onPick(e) {
  const file = e.target.files?.[0]
  if (!file) return
  uploadFile(file)
}

function uploadFile(file) {
  const csrf = window.csrf_token || window.frappe?.csrf_token
  if (!csrf) {
    props.onUploadEnd?.({ ok: false, error: "Missing CSRF token" })
    return
  }

  props.onUploadStart?.()

  const form = new FormData()
  form.append("file", file)
  form.append("is_private", "0")

  const xhr = new XMLHttpRequest()
  xhr.open("POST", "/api/method/upload_file", true)

  // CSRF header that Frappe requires
  xhr.setRequestHeader("X-Frappe-CSRF-Token", csrf)

  // Same-origin already includes cookies, but leaving this doesn't hurt
  xhr.withCredentials = true

  xhr.upload.onprogress = (evt) => {
    if (!evt.lengthComputable) return
    const percent = Math.round((evt.loaded / evt.total) * 100)
    props.onUploadProgress?.({ percent, loaded: evt.loaded, total: evt.total })
  }

  xhr.onerror = () => {
    props.onUploadEnd?.({ ok: false, error: "Network error" })
  }

  xhr.onload = () => {
    let res
    try {
      res = JSON.parse(xhr.responseText)
    } catch {
      props.onUploadEnd?.({ ok: false, error: "Bad JSON response" })
      return
    }

    if (xhr.status >= 200 && xhr.status < 300 && res.message) {
      props.onFileUploaded({
        file_url: res.message.file_url,
        file_type: res.message.file_type || file.name.split(".").pop(),
      })
      props.onUploadEnd?.({ ok: true })
    } else {
      props.onUploadEnd?.({
        ok: false,
        error: res?.exception || res?._server_messages || "Upload failed",
      })
    }
  }

  xhr.send(form)
}
</script>