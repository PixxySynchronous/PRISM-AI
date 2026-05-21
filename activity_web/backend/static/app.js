const tabButtons = Array.from(document.querySelectorAll(".tab-button"));
const tabPanels = Array.from(document.querySelectorAll(".tab-panel"));

const activityForm = document.getElementById("upload-form");
const videoInput = document.getElementById("video-input");
const fileLabel = document.getElementById("file-label");
const statusBox = document.getElementById("status");
const activityProgress = document.getElementById("activity-progress");
const resultsBox = document.getElementById("results");
const metricsBox = document.getElementById("metrics");
const studentGroupsBox = document.getElementById("student-groups");
const emptyStateBox = document.getElementById("empty-state");
const summaryLink = document.getElementById("summary-link");
const csvLink = document.getElementById("csv-link");
const annotatedLink = document.getElementById("annotated-link");
const processOutput = document.getElementById("process-output");
const activityProgressFill = document.getElementById("activity-progress-fill");
const activityProgressText = document.getElementById("activity-progress-text");

const enrollForm = document.getElementById("enroll-form");
const studentNameInput = document.getElementById("student-name-input");
const enrollMediaInput = document.getElementById("enroll-media-input");
const enrollMediaLabel = document.getElementById("enroll-media-label");
const enrollStatus = document.getElementById("enroll-status");
const enrollProgress = document.getElementById("enroll-progress");
const enrollResult = document.getElementById("enroll-result");

const markForm = document.getElementById("mark-form");
const classroomPhotoInput = document.getElementById("classroom-photo-input");
const classroomPhotoLabel = document.getElementById("classroom-photo-label");
const markStatus = document.getElementById("mark-status");
const markProgress = document.getElementById("mark-progress");
const markResult = document.getElementById("mark-result");
const markedPhotoPreview = document.getElementById("marked-photo-preview");
const markedPhotoLink = document.getElementById("marked-photo-link");
const recognizedList = document.getElementById("recognized-list");
const attendanceLogList = document.getElementById("attendance-log-list");
const rosterList = document.getElementById("roster-list");
const attendanceLogSummary = document.getElementById("attendance-log-summary");
const rosterProgress = document.getElementById("roster-progress");
const PROCESS_POLL_INTERVAL_MS = 2000;

function activateTab(tabId) {
  tabButtons.forEach((button) => {
    const isActive = button.dataset.tabTarget === tabId;
    button.classList.toggle("active", isActive);
    button.setAttribute("aria-selected", String(isActive));
  });

  tabPanels.forEach((panel) => {
    panel.classList.toggle("hidden", panel.id !== tabId);
  });
}

tabButtons.forEach((button) => {
  button.addEventListener("click", () => activateTab(button.dataset.tabTarget));
});

function selectedFileText(files, fallbackText) {
  if (!files || files.length === 0) {
    return fallbackText;
  }
  if (files.length === 1) {
    return files[0].name;
  }
  return `${files[0].name} + ${files.length - 1} more`;
}

function setProgress(progressElement, active) {
  if (!progressElement) {
    return;
  }

  progressElement.classList.toggle("hidden", !active);
  progressElement.setAttribute("aria-hidden", String(!active));
}

videoInput.addEventListener("change", () => {
  fileLabel.textContent = selectedFileText(videoInput.files, "Choose a video file or drag one here");
});

enrollMediaInput.addEventListener("change", () => {
  enrollMediaLabel.textContent = selectedFileText(enrollMediaInput.files, "Choose photos or a video for enrollment");
});

classroomPhotoInput.addEventListener("change", () => {
  classroomPhotoLabel.textContent = selectedFileText(classroomPhotoInput.files, "Choose a classroom photo");
});

activityForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  if (!videoInput.files.length) {
    statusBox.textContent = "Choose a video file first.";
    statusBox.classList.add("error");
    return;
  }

  const submitButton = activityForm.querySelector("button[type='submit']");
  const payload = new FormData();
  payload.append("video", videoInput.files[0]);

  resultsBox.classList.add("hidden");
  statusBox.classList.remove("error");
  statusBox.textContent = "Processing video. This can take a while...";
  submitButton.disabled = true;
  setProgress(activityProgress, true);

  try {
    const response = await fetch("/api/process", {
      method: "POST",
      body: payload,
    });
    const data = await response.json();

    if (!response.ok || !data.ok) {
      throw new Error(data.error || "Processing failed.");
    }

    statusBox.textContent = "Video job queued. Waiting for the pipeline to finish...";
    await waitForProcessJob(data.status_url || `/api/process/${encodeURIComponent(data.job_id)}`);
  } catch (error) {
    statusBox.textContent = error.message;
    statusBox.classList.add("error");
  } finally {
    submitButton.disabled = false;
    setProgress(activityProgress, false);
  }
});

enrollForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  const studentName = studentNameInput.value.trim();
  if (!studentName) {
    enrollStatus.textContent = "Enter a student name.";
    enrollStatus.classList.add("error");
    return;
  }

  if (!enrollMediaInput.files.length) {
    enrollStatus.textContent = "Upload one or more photos or a video.";
    enrollStatus.classList.add("error");
    return;
  }

  const submitButton = enrollForm.querySelector("button[type='submit']");
  const payload = new FormData();
  payload.append("student_name", studentName);
  Array.from(enrollMediaInput.files).forEach((file) => payload.append("media", file));

  enrollStatus.classList.remove("error");
  enrollStatus.textContent = "Extracting embeddings and saving the student...";
  submitButton.disabled = true;
  setProgress(rosterProgress, true);

  try {
    const response = await fetch("/api/attendance/enroll", {
      method: "POST",
      body: payload,
    });
    const data = await response.json();

    if (!response.ok || !data.ok) {
      throw new Error(data.error || "Enrollment failed.");
    }

    renderRoster(data.students || []);
    renderEnrollmentResult(data.student, data.media_samples || []);
    enrollStatus.textContent = `Enrolled ${data.student.name} successfully.`;
    await refreshAttendanceSummary(enrollProgress);
  } catch (error) {
    enrollStatus.textContent = error.message;
    enrollStatus.classList.add("error");
  } finally {
    submitButton.disabled = false;
    setProgress(enrollProgress, false);
  }
});

markForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  if (!classroomPhotoInput.files.length) {
    markStatus.textContent = "Upload a classroom photo first.";
    markStatus.classList.add("error");
    return;
  }

  const submitButton = markForm.querySelector("button[type='submit']");
  const payload = new FormData();
  payload.append("photo", classroomPhotoInput.files[0]);

  markStatus.classList.remove("error");
  markStatus.textContent = "Detecting faces and marking attendance...";
  submitButton.disabled = true;
  setProgress(markProgress, true);

  try {
    const response = await fetch("/api/attendance/mark", {
      method: "POST",
      body: payload,
    });
    const data = await response.json();

    if (!response.ok || !data.ok) {
      throw new Error(data.error || "Attendance marking failed.");
    }

    renderMarkedPhoto(data.marked_data_url, data.marked_url);
    renderRecognizedFaces(data.recognized || [], data.unknown_faces || 0);
    renderAttendanceLog(data.attendance_log || []);
    renderRoster(data.roster || []);
    markStatus.textContent = `Marked attendance for ${data.recognized.length} student${data.recognized.length === 1 ? "" : "s"}.`;
    markResult.classList.remove("hidden");
    await refreshAttendanceSummary(markProgress);
  } catch (error) {
    markStatus.textContent = error.message;
    markStatus.classList.add("error");
  } finally {
    submitButton.disabled = false;
    setProgress(markProgress, false);
  }
});

async function refreshAttendanceSummary(progressElement = null) {
  setProgress(progressElement, true);
  try {
    const response = await fetch("/api/attendance/roster");
    const data = await response.json();
    if (response.ok && data.ok) {
      renderRoster(data.students || []);
      renderAttendanceSummary(data.attendance || []);
    }
  } catch (error) {
    console.error(error);
  } finally {
    setProgress(progressElement, false);
  }
}

async function waitForProcessJob(statusUrl) {
  while (true) {
    const response = await fetch(statusUrl, { cache: "no-store" });
    const data = await response.json();

    if (!response.ok || !data.ok) {
      throw new Error(data.error || "Unable to fetch job status.");
    }

    if (data.status === "queued" || data.status === "running") {
      statusBox.textContent = data.status === "queued" ? "Video job queued. Processing will start shortly..." : "Processing video. This can take a while...";
      renderActivityProgress(data.progress || null);
      renderProcessOutput(data.log_tail || data.console_output || "");
      await delay(PROCESS_POLL_INTERVAL_MS);
      continue;
    }

    if (data.status === "failed") {
      throw new Error(data.error || "Processing failed.");
    }

    if (data.status === "completed") {
      renderActivityProgress(data.progress || null);
      renderMetrics(data.summary, data.job_id);
      renderLinks(data.download_urls || {});
      renderGroupedStudents(data.clips || []);
      renderProcessOutput(data.console_output || "");
      statusBox.textContent = "Done. Review the summary below.";
      resultsBox.classList.remove("hidden");
      return;
    }

    throw new Error(`Unknown job status: ${data.status}`);
  }
}

function delay(milliseconds) {
  return new Promise((resolve) => setTimeout(resolve, milliseconds));
}

function renderProcessOutput(consoleOutput) {
  if (!processOutput) {
    return;
  }

  if (!consoleOutput) {
    processOutput.classList.add("hidden");
    processOutput.textContent = "";
    return;
  }

  processOutput.textContent = consoleOutput;
  processOutput.classList.remove("hidden");
}

function renderActivityProgress(progress) {
  if (!activityProgressFill || !activityProgressText) {
    return;
  }

  if (!progress || progress.current_frame === undefined || progress.total_frames === undefined) {
    activityProgressFill.style.width = "0%";
    activityProgressText.classList.add("hidden");
    activityProgressText.textContent = "";
    return;
  }

  const currentFrame = Number(progress.current_frame) || 0;
  const totalFrames = Number(progress.total_frames) || 0;
  const percent = Number(progress.percent);
  const displayPercent = Number.isFinite(percent) ? percent : totalFrames > 0 ? (currentFrame / totalFrames) * 100 : 0;
  const clampedPercent = Math.max(0, Math.min(100, displayPercent));

  activityProgressFill.style.width = `${clampedPercent}%`;
  activityProgressText.textContent = totalFrames > 0 ? `${currentFrame} / ${totalFrames} frames processed (${clampedPercent.toFixed(1)}%)` : `${currentFrame} frames processed`;
  activityProgressText.classList.remove("hidden");
}

function renderMetrics(summary, jobId) {
  const items = [
    ["Job", jobId],
    ["Video", summary.video_name],
    ["Clips", summary.clip_count],
    ["Students", summary.student_count],
    ["Frames", summary.total_frames],
  ];

  metricsBox.innerHTML = items
    .map(([label, value]) => `<div class="metric"><span class="label">${label}</span><span class="value">${value ?? "-"}</span></div>`)
    .join("");
}

function renderLinks(downloadUrls) {
  summaryLink.href = downloadUrls.summary_json || "#";
  csvLink.href = downloadUrls.csv || "#";
  annotatedLink.href = downloadUrls.annotated_video || "#";
}

function renderGroupedStudents(clips) {
  const grouped = groupClipsByStudent(clips);

  if (grouped.length === 0) {
    studentGroupsBox.innerHTML = "";
    emptyStateBox.classList.remove("hidden");
    return;
  }

  emptyStateBox.classList.add("hidden");
  studentGroupsBox.innerHTML = grouped
    .map(
      ({ studentLabel, clips: studentClips }) => `
        <section class="student-card">
          <div class="student-card-header">
            <div>
              <p class="student-title">${studentLabel}</p>
              <p class="student-meta">${studentClips.length} engagement clip${studentClips.length === 1 ? "" : "s"}</p>
            </div>
          </div>
          <div class="clip-gallery">
            ${studentClips
              .map(
                (clip) => `
                  <article class="clip-card">
                    <video class="clip-player" controls preload="metadata" src="${clip.clip_url || ""}"></video>
                    <div class="clip-card-body">
                      <div class="clip-badges">
                        <span class="clip-badge ${clip.decision_source === "phone_detector" ? "clip-badge-phone" : "clip-badge-cnn"}">${clip.decision_source || "3dcnn"}</span>
                        <span class="clip-badge">${formatWindow(clip.window_start_seconds)}</span>
                      </div>
                      <p class="clip-summary">${clip.predicted_label ?? "-"} · confidence ${formatNumber(clip.confidence)}</p>
                      <p class="clip-detail">Low ${formatNumber(clip.low_engagement)} · High ${formatNumber(clip.high_engagement)}</p>
                      <a class="clip-link" href="${clip.clip_url || "#"}" target="_blank" rel="noreferrer">Open clip</a>
                    </div>
                  </article>
                `,
              )
              .join("")}
          </div>
          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Window</th>
                  <th>Label</th>
                  <th>Confidence</th>
                  <th>Low</th>
                  <th>High</th>
                  <th>Decision</th>
                </tr>
              </thead>
              <tbody>
                ${studentClips
                  .map(
                    (clip) => `
                      <tr>
                        <td>${formatWindow(clip.window_start_seconds)}</td>
                        <td>${clip.predicted_label ?? "-"}</td>
                        <td>${formatNumber(clip.confidence)}</td>
                        <td>${formatNumber(clip.low_engagement)}</td>
                        <td>${formatNumber(clip.high_engagement)}</td>
                        <td>${clip.decision_source || "3dcnn"}</td>
                      </tr>
                    `,
                  )
                  .join("")}
              </tbody>
            </table>
          </div>
        </section>
      `,
    )
    .join("");
}

function groupClipsByStudent(clips) {
  const bucket = new Map();

  clips
    .slice()
    .sort((left, right) => {
      const leftStudent = studentSortKey(left);
      const rightStudent = studentSortKey(right);
      if (leftStudent !== rightStudent) {
        return leftStudent.localeCompare(rightStudent, undefined, { numeric: true, sensitivity: "base" });
      }
      return Number(left.window_start_seconds ?? 0) - Number(right.window_start_seconds ?? 0);
    })
    .forEach((clip) => {
      const key = studentSortKey(clip);
      if (!bucket.has(key)) {
        bucket.set(key, []);
      }
      bucket.get(key).push(clip);
    });

  return Array.from(bucket.entries()).map(([studentLabel, studentClips]) => ({ studentLabel, clips: studentClips }));
}

function studentSortKey(clip) {
  if (clip.student_label) {
    return clip.student_label;
  }
  if (clip.student_id !== null && clip.student_id !== undefined) {
    return `student_${String(clip.student_id).padStart(3, "0")}`;
  }
  return "Unknown student";
}

function renderEnrollmentResult(student, mediaSamples) {
  if (!student) {
    enrollResult.classList.add("hidden");
    return;
  }

  enrollResult.classList.remove("hidden");
  enrollResult.innerHTML = `
    <div class="result-summary">${student.name} enrolled successfully.</div>
    <div class="result-detail">Observations: ${student.observations ?? 0}</div>
    <div class="result-detail">Media samples: ${mediaSamples.map((sample) => `${sample.file_name} (${sample.frame_samples})`).join(", ")}</div>
  `;
}

function renderMarkedPhoto(previewUrl, openUrl) {
  if (!previewUrl && !openUrl) {
    markResult.classList.add("hidden");
    return;
  }

  markResult.classList.remove("hidden");
  markedPhotoLink.href = openUrl || previewUrl;

  if (previewUrl && previewUrl.startsWith("data:")) {
    markedPhotoPreview.src = previewUrl;
    return;
  }

  markedPhotoPreview.removeAttribute("src");

  const sourceUrl = previewUrl || openUrl;
  fetch(sourceUrl)
    .then((response) => {
      if (!response.ok) {
        throw new Error(`Unable to load annotated photo (${response.status})`);
      }
      return response.blob();
    })
    .then((blob) => {
      const objectUrl = URL.createObjectURL(blob);
      markedPhotoPreview.onload = () => URL.revokeObjectURL(objectUrl);
      markedPhotoPreview.onerror = () => URL.revokeObjectURL(objectUrl);
      markedPhotoPreview.src = objectUrl;
    })
    .catch((error) => {
      console.error(error);
      markedPhotoPreview.alt = "Annotated photo could not be loaded. Use the link to open it directly.";
    });
}

function renderRecognizedFaces(recognized, unknownFaces) {
  const recognizedRows = recognized.length
    ? recognized
        .map(
          (entry) => `
            <div class="result-item">
              <strong>${entry.student.name}</strong>
              <span>Confidence ${formatNumber(entry.confidence)}</span>
            </div>
          `,
        )
        .join("")
    : '<div class="result-item muted">No enrolled students recognized.</div>';

  recognizedList.innerHTML = `
    <h3>Recognized faces</h3>
    ${recognizedRows}
    <div class="result-item muted">Unknown faces: ${unknownFaces}</div>
  `;
}

function renderAttendanceLog(attendanceLog) {
  attendanceLogList.innerHTML = `
    <h3>Attendance log</h3>
    ${attendanceLog
      .map(
        (entry) => `
          <div class="result-item">
            <strong>${entry.student_name}</strong>
            <span>${entry.recognized_at} · ${entry.source} · ${formatNumber(entry.confidence)}</span>
          </div>
        `,
      )
      .join("")}
  `;
}

function renderAttendanceSummary(attendanceLog) {
  attendanceLogSummary.innerHTML = `
    <h3>Recent attendance activity</h3>
    ${attendanceLog
      .map(
        (entry) => `
          <div class="result-item">
            <strong>${entry.student_name}</strong>
            <span>${entry.recognized_at} · ${formatNumber(entry.confidence)}</span>
          </div>
        `,
      )
      .join("")}
  `;
}

function renderRoster(students) {
  if (!students.length) {
    rosterList.innerHTML = '<div class="result-item muted">No students enrolled yet.</div>';
    return;
  }

  rosterList.innerHTML = students
    .map(
      (student) => `
        <div class="roster-item" data-student-id="${student.student_id}">
          <div class="roster-item-main">
            <strong>${student.name}</strong>
            <span>${student.observations ?? 0} embeddings · updated ${student.updated_at ?? "-"}</span>
          </div>
          <button class="delete-student-button" type="button" data-student-id="${student.student_id}">Delete</button>
        </div>
      `,
    )
    .join("");
}

rosterList.addEventListener("click", async (event) => {
  const button = event.target.closest(".delete-student-button");
  if (!button) {
    return;
  }

  const studentId = button.dataset.studentId;
  if (!studentId) {
    return;
  }

  const studentCard = button.closest(".roster-item");
  const studentName = studentCard?.querySelector("strong")?.textContent || "this student";
  const confirmed = window.confirm(`Delete ${studentName}? This will remove the student and their attendance records.`);
  if (!confirmed) {
    return;
  }

  button.disabled = true;
  button.textContent = "Deleting...";
  setProgress(enrollProgress, true);

  try {
    const response = await fetch(`/api/attendance/students/${encodeURIComponent(studentId)}`, {
      method: "DELETE",
    });
    const data = await response.json();

    if (!response.ok || !data.ok) {
      throw new Error(data.error || "Delete failed.");
    }

    renderRoster(data.students || []);
    renderAttendanceSummary(data.attendance || []);
    enrollStatus.classList.remove("error");
    markStatus.classList.remove("error");
    await refreshAttendanceSummary(rosterProgress);
  } catch (error) {
    alert(error.message);
  } finally {
    button.disabled = false;
    button.textContent = "Delete";
    setProgress(rosterProgress, false);
  }
});

function formatWindow(seconds) {
  const numericSeconds = Number(seconds);
  if (Number.isNaN(numericSeconds)) {
    return "-";
  }
  return `${numericSeconds.toFixed(2)}s`;
}

function formatNumber(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "-";
  }
  return Number(value).toFixed(4);
}

refreshAttendanceSummary();
