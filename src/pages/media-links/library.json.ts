import libraryPayload from "../../data/library.json";

export const prerender = true;

export function GET() {
  return new Response(JSON.stringify(libraryPayload, null, 2), {
    headers: {
      "content-type": "application/json; charset=utf-8",
    },
  });
}
