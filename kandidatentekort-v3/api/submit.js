export const config = {
  runtime: 'edge',
};

export default async function handler(req) {
  if (req.method !== 'POST') {
    return new Response(JSON.stringify({ error: 'Method Not Allowed' }), { 
      status: 405,
      headers: { 'Content-Type': 'application/json' }
    });
  }

  try {
    const formData = await req.formData();
    const voornaam = formData.get('voornaam');
    const achternaam = formData.get('achternaam');
    const email = formData.get('email');
    const telefoon = formData.get('telefoon');
    const file = formData.get('file');

    if (!file || !file.name) {
      throw new Error("Geen geldig bestand geüpload.");
    }

    const supabaseUrl = process.env.SUPABASE_URL;
    const supabaseKey = process.env.SUPABASE_SERVICE_KEY || process.env.SUPABASE_ANON_KEY;

    if (!supabaseUrl || !supabaseKey) {
        throw new Error("Server configuration error: parameters ontbreken.");
    }

    // 1. Upload File to Supabase Storage (bucket: vacatures)
    const safeFileName = file.name.replace(/[^a-zA-Z0-9.\-_]/g, '_');
    const uniqueFileName = `${Date.now()}_${safeFileName}`;
    const fileBuffer = await file.arrayBuffer();
    
    const storageRes = await fetch(`${supabaseUrl}/storage/v1/object/vacatures/${uniqueFileName}`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${supabaseKey}`,
        'apikey': supabaseKey,
        'Content-Type': file.type || 'application/octet-stream',
      },
      body: fileBuffer
    });
    
    if (!storageRes.ok) {
        const err = await storageRes.text();
        throw new Error(`Storage upload failed: ${err}`);
    }

    const fileUrl = `${supabaseUrl}/storage/v1/object/public/vacatures/${uniqueFileName}`;

    // 2. Insert into kt_leads table
    const dbRes = await fetch(`${supabaseUrl}/rest/v1/kt_leads`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${supabaseKey}`,
        'apikey': supabaseKey,
        'Content-Type': 'application/json',
        'Prefer': 'return=minimal'
      },
      body: JSON.stringify({
        first_name: voornaam || '',
        last_name: achternaam || '',
        email: email || '',
        phone: telefoon || '',
        file_url: fileUrl,
        raw_vacancy_text: null, // AI will populate this if we extract PDF text later, or leave null
        status: 'pending_ai',
        source: 'kandidatentekort-v3'
      })
    });

    if (!dbRes.ok) {
        const err = await dbRes.text();
        throw new Error(`Database insert failed: ${err}`);
    }

    return new Response(JSON.stringify({ success: true, file_url: fileUrl }), { 
      status: 200, 
      headers: { 'Content-Type': 'application/json' } 
    });

  } catch (error) {
    console.error("Webhook Error:", error);
    return new Response(JSON.stringify({ error: error.message }), { 
      status: 500, 
      headers: { 'Content-Type': 'application/json' } 
    });
  }
}
