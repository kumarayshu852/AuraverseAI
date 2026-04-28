const express = require('express');
const cors = require('cors');
const fs = require('fs');
const app = express();

app.use(cors());
app.use(express.json());

const MEMORY_FILE = "memory.json";

// ✅ Safe memory read — empty ya corrupt file crash nahi karegi
function readMemory() {
    try {
        const content = fs.readFileSync(MEMORY_FILE, 'utf8').trim();
        if (!content) return { facts: [] };
        return JSON.parse(content);
    } catch (e) {
        console.log("⚠️ memory.json corrupt/empty, reset kar rahe hain...");
        return { facts: [] };
    }
}

// ✅ Safe memory write
function writeMemory(data) {
    fs.writeFileSync(MEMORY_FILE, JSON.stringify(data, null, 2));
}

// File exist nahi hai toh banao
if (!fs.existsSync(MEMORY_FILE)) {
    writeMemory({ facts: [] });
}

// Memory save karne ka route
app.post('/remember', (req, res) => {
    const { fact } = req.body;
    if (!fact) return res.status(400).json({ message: "Fact missing!", status: "error" });

    let data = readMemory();
    data.facts.push(fact);
    writeMemory(data);
    res.json({ message: "Memory Updated!", status: "success" });
});

// Memory fetch karne ka route
app.get('/recall', (req, res) => {
    let data = readMemory();
    res.json({ memory: data.facts.join(". "), facts: data.facts });
});

// Memory clear karne ka route (bonus)
app.delete('/clear', (req, res) => {
    writeMemory({ facts: [] });
    res.json({ message: "Memory cleared!", status: "success" });
});

app.listen(3000, () => {
    console.log("🧠 Node.js Memory Server is running on port 3000");
});