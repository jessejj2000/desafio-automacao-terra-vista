const express = require('express');

const app = express();
const port = 4000;

app.get('/proxy', async (req, res) => {
    const targetUrl = req.query.url;
    if (!targetUrl) return res.status(400).send("url parameter is required");
    
    console.log("Fetching:", targetUrl);
    try {
        const response = await fetch(targetUrl, {
            headers: {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'application/pdf,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5'
            }
        });
        
        if (!response.ok) {
            console.error(`Failed to fetch: ${response.status} ${response.statusText}`);
            return res.status(response.status).send(response.statusText);
        }
        
        const buffer = await response.arrayBuffer();
        res.setHeader('Content-Type', 'application/pdf');
        res.send(Buffer.from(buffer));
        console.log("Success fetching:", targetUrl);
    } catch (e) {
        console.error("Error fetching:", e.message);
        res.status(500).send(e.message);
    }
});

app.listen(port, () => {
    console.log(`Local proxy running on port ${port}`);
});
