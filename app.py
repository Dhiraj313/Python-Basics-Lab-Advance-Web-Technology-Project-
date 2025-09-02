from flask import Flask, render_template, abort

app = Flask(__name__)

# sample lessons (slug used in URL)
lessons = [
    {
        "id": 1,
        "title": "Introduction to Python",
        "description": "Learn Python basics: variables, types, printing.",
        "slug": "introduction-to-python",
        "thumbnail": "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?auto=format&fit=crop&w=800&q=80"
    },
    {
        "id": 2,
        "title": "Control Structures",
        "description": "If, else, loops and branching logic.",
        "slug": "control-structures",
        "thumbnail": "https://images.unsplash.com/photo-1515879218367-8466d910aaa4?auto=format&fit=crop&w=800&q=80"
    },
    {
        "id": 3,
        "title": "Functions",
        "description": "Define and reuse code with functions.",
        "slug": "functions",
        "thumbnail": "https://images.unsplash.com/photo-1555066931-4365d14bab8c?auto=format&fit=crop&w=800&q=80"
    },
    {
        "id": 4,
        "title": "Lists & Dictionaries",
        "description": "Work with lists, dicts and iterate over data.",
        "slug": "lists-and-dictionaries",
        "thumbnail": "https://images.unsplash.com/photo-1519389950473-47ba0277781c?auto=format&fit=crop&w=800&q=80"
    },
    {
        "id": 5,
        "title": "File Handling",
        "description": "Read and write files, handle exceptions safely.",
        "slug": "file-handling",
        "thumbnail": "https://images.unsplash.com/photo-1498050108023-c5249f4df085?auto=format&fit=crop&w=800&q=80"
    },
]

@app.route("/")
def index():
    return render_template("index.html", lessons=lessons)

@app.route("/lesson/<slug>")
def lesson(slug):
    lesson = next((l for l in lessons if l["slug"] == slug), None)
    if not lesson:
        abort(404)
    return render_template("lesson.html", lesson=lesson)

if __name__ == "__main__":
    app.run(debug=True)
