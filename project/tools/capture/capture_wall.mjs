import puppeteer from '/home/m0/Videos/fixbyte-studio-promo/project/node_modules/puppeteer-core/lib/puppeteer/puppeteer-core.js';
const exe='/home/m0/.cache/puppeteer/chrome-headless-shell/linux-145.0.7632.77/chrome-headless-shell-linux64/chrome-headless-shell';
const out=process.argv[2]; const list=process.argv.slice(3);
const b=await puppeteer.launch({executablePath:exe,args:['--no-sandbox','--hide-scrollbars']});
await Promise.all(list.map(async (u)=>{
  const p=await b.newPage(); await p.setViewport({width:1920,height:1080,deviceScaleFactor:1});
  const name=new URL(u).hostname.split('.')[0];
  try{
    await p.goto(u,{waitUntil:'networkidle2',timeout:45000});
    await new Promise(r=>setTimeout(r,5000));
    await p.evaluate(()=>{document.querySelectorAll('#__framer-badge-container,[id*=badge]').forEach(e=>e.remove());});
    await p.screenshot({path:`${out}/${name}.png`});
    console.log('ok',name);
  }catch(e){console.log('fail',name,e.message)}
  await p.close();
}));
await b.close();
