import streamsPayload from "../../data/streams.json";

export const prerender = true;

export function GET() {
  return new Response(JSON.stringify(streamsPayload, null, 2), {
    headers: {
      "content-type": "application/json; charset=utf-8",
    },
  });
}
