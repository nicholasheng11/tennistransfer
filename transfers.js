// transfers.js — THIS is the only file you edit to curate the tracker.
//
// To add a player: copy one { ... } block below, paste it at the top of the list,
// change the values, and make sure there's a comma after the closing } .
//
// Rules:
//   - status must be EXACTLY one of: "In Portal", "Committed", "Signed", "Withdrawn"
//   - leave newSchool as ""  until the player commits somewhere
//   - hometown is where the player is from, e.g. "Madrid, Spain" (leave "" if unknown)
//   - dateUpdated is NOT shown on the card anymore, but it still controls the order
//     (newest first), so keep setting it to the date you add or update someone
//   - give every player a unique id (just use the next number)

const TRANSFERS = [
  { id: "13", name: "Thomas Nelson", status: "Committed", previousSchool: "Old Dominion", newSchool: "Michigan State", hometown: "", classYear: "Jr.", dateUpdated: "2026-05-27" },
  { id: "14", name: "Ashton Adesoro", status: "Signed", previousSchool: "Western Michigan", newSchool: "Miami (FL)", hometown: "", classYear: "Sr.", dateUpdated: "2026-05-27" },
  { id: "12", name: "Hamza Nasridinov",    status: "Signed",  previousSchool: "Auburn",  newSchool: "Texas A&M",    hometown: "", classYear: "Jr.", dateUpdated: "2026-05-26" },
  { id: "4",  name: "Nicholas Heng",      status: "Signed",  previousSchool: "Auburn", newSchool: "Michigan",        hometown: "", classYear: "R-Sr.", dateUpdated: "2026-05-26" },
  { id: "2",  name: "Alan Bojarski",     status: "Signed",  previousSchool: "Auburn", newSchool: "Tennessee",         hometown: "", classYear: "Jr.", dateUpdated: "2026-05-25" },
  { id: "10", name: "Oscar Lacides",   status: "Committed",  previousSchool: "Oklahoma",  newSchool: "Tennessee",          hometown: "", classYear: "Sr.", dateUpdated: "2026-05-25" },
  { id: "1",  name: "Orel Kihmi",       status: "Committed",  previousSchool: "Oklahoma",   newSchool: "Tennessee",    hometown: "", classYear: "Jr.", dateUpdated: "2026-05-24" },
  { id: "8",  name: "Hank Trondson",       status: "Committed",  previousSchool: "Oklahoma",  newSchool: "Oklahoma State",          hometown: "", classYear: "Jr.", dateUpdated: "2026-05-23" },
  { id: "5",  name: "Jan Kobierski",    status: "Committed",  previousSchool: "Tennessee", newSchool: "San Diego State",   hometown: "", classYear: "Jr.", dateUpdated: "2026-05-22" },
  { id: "9",  name: "Piotr Siekanowicz",     status: "Committed",  previousSchool: "Tennessee",  newSchool: "San Diego State", hometown: "", classYear: "Jr.", dateUpdated: "2026-05-21" },
  { id: "3",  name: "Ariel Zauber",  status: "Committed",     previousSchool: "Wake Forest",     newSchool: "Indiana",       hometown: "", classYear: "Jr.", dateUpdated: "2026-05-20" },
  { id: "7",  name: "Blake Anderson",     status: "Signed",     previousSchool: "Baylor",       newSchool: "San Diego State",  hometown: "", classYear: "So.", dateUpdated: "2026-05-19" },
  { id: "6",  name: "Mats Bredschneijder",     status: "Committed",  previousSchool: "VCU",    newSchool: "Hawaii",          hometown: "", classYear: "Jr.", dateUpdated: "2026-05-18" },
  { id: "11", name: "Arsene Pougault",     status: "Signed",     previousSchool: "Arkansas, Charlotte",  newSchool: "Boise State",   hometown: "", classYear: "Jr.", dateUpdated: "2026-05-17" },
];
