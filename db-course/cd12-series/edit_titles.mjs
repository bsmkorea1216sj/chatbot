import { FileBlob, PresentationFile } from '@oai/artifact-tool';
import fs from 'node:fs/promises';

// Edit exact existing subtitle shapes through the imported-deck API.
// The serialization-preserving XML patch applies these strings to originals,
// keeping lecturer media, masters, notes, embedded objects and run styling.
const edits=[];
for (const p of [1,2,3]) {
 const deck=await PresentationFile.importPptx(await FileBlob.load(new URL(`./part${p}.pptx`,import.meta.url).pathname));
 const slide=deck.slides.items[1];
 const old=p===1?'미니 쇼핑몰 DB 설계와 웹앱 실습':'시나리오 기반 설계 실습';
 const replacement=p===1?'액세서리몰 DB 설계와 웹앱 실습':'여성 액세서리몰 설계 실습';
 let count=0;
 for(const shape of slide.shapes.items){
  if(shape.text && String(shape.text).includes(old)){
   shape.text.replace(old,replacement); count++;
  }
 }
 edits.push({part:p,old,replacement,count});
 console.log(JSON.stringify(edits.at(-1)));
}
await fs.writeFile(new URL('./title-edit-plan.json',import.meta.url),JSON.stringify(edits,null,2));
