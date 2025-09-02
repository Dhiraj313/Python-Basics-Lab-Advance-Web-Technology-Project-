
async function runCode(section) {
  const textarea = section.querySelector("textarea.code");
  const output = section.querySelector(".output");
  const tests = JSON.parse(section.getAttribute("data-tests") || "null");
  output.textContent = "Running...";
  try {
    const res = await fetch("/run", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({ code: textarea.value, tests })
    });
    const data = await res.json();
    let text = "";
    if (data.stdout) text += data.stdout + (data.stdout.endsWith("\n") ? "" : "\n");
    if (!data.ok) {
      text += `\n❌ ${data.error || "Failed."}`;
    } else {
      text += "✅ Passed";
    }
    if (Array.isArray(data.tests) && data.tests.length) {
      text += "\n\nTest details:\n" + JSON.stringify(data.tests, null, 2);
    }
    output.textContent = text.trim();
  } catch (e) {
    output.textContent = "Error calling server: " + e.message;
  }
}

function setupExercise(section) {
  const runBtn = section.querySelector(".btn.run");
  const resetBtn = section.querySelector(".btn.reset");
  const showSolutionBtn = section.querySelector(".btn.show-solution");
  const textarea = section.querySelector("textarea.code");
  const starter = textarea.value;
  runBtn.addEventListener("click", () => runCode(section));
  resetBtn.addEventListener("click", () => { textarea.value = starter; });
  if (showSolutionBtn) {
    const details = section.querySelector("details.solution");
    showSolutionBtn.addEventListener("click", () => {
      details.open = !details.open;
    });
  }
}

window.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("section.exercise").forEach(setupExercise);
});
