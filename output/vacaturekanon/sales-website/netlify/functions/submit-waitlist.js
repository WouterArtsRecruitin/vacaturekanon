const fetch = require('node-fetch').default || global.fetch;

exports.handler = async function(event, context) {
  try {
    const params = new URLSearchParams(event.body);
    const data = Object.fromEntries(params.entries());
    
    console.log("Direct Function Form Submission:", data);

    const campaignId = "cam_zs4iGwL4poCxTt86Y";
    const apiKey = "4c075a8a91a4e7eb6a609a3d2da5b13b";
    
    const lemlistPayload = {
      email: data.email,
      firstName: data.voornaam || "Topvlieger",
      lastName: data.achternaam || "",
      companyName: data.bedrijfsnaam || "Onbekend B2B",
      phone: data.telefoonnummer || "",
      tags: ["waitlist", "v2_direct_api"]
    };

    console.log("Pushing direct to Lemlist...", lemlistPayload);

    const response = await fetch(`https://api.lemlist.com/api/campaigns/${campaignId}/leads`, {
      method: "POST",
      headers: {
        "Authorization": "Basic " + Buffer.from(":" + apiKey).toString("base64"),
        "Content-Type": "application/json"
      },
      body: JSON.stringify(lemlistPayload)
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error("Lemlist Direct Push Failed:", errorText);
      return { statusCode: 500, body: "Lemlist API Fout." };
    }

    console.log("BAM! Lead directly synced to Lemlist:", data.email);
    
    return {
      statusCode: 200,
      body: "Succesvol overgedragen."
    };
  } catch (error) {
    console.error("Serverless API Route Error:", error);
    return {
      statusCode: 500,
      body: "Systeemfout."
    };
  }
};
