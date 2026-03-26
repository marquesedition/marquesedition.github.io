import reelsPayload from "../../data/reels.json";

export const prerender = true;

export function GET() {
  return new Response(JSON.stringify(reelsPayload, null, 2), {
    headers: {
      "content-type": "application/json; charset=utf-8",
    },
  });
}
