import eventsPayload from "../../data/events.json";

export const prerender = true;

export function GET() {
  return new Response(JSON.stringify(eventsPayload, null, 2), {
    headers: {
      "content-type": "application/json; charset=utf-8",
    },
  });
}
