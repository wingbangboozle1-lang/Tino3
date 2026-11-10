(function(){
  var f=document.getElementById('p19');if(!f)return;
  function n(id){return Math.max(0,parseFloat(document.getElementById(id).value)||0)}
  function r10(x){return Math.round(x/10)*10}
  function fmt(x){return '$'+r10(x).toLocaleString('en-US')}
  function go(){
    var mv=n('p19-mv'),bv=n('p19-bv'),add=n('p19-add'),rate=n('p19-rate')/100;
    var live=bv+Math.max(0,mv-(bv+add));
    document.getElementById('p19-out').innerHTML=
      'Taxable value if the heir lives there: '+fmt(live)+' (about '+fmt(live*rate)+' a year)<br>'+
      'Taxable value if nobody eligible lives there: '+fmt(mv)+' (about '+fmt(mv*rate)+' a year)<br>'+
      'Yearly difference: '+fmt((mv-live)*rate);
  }
  f.addEventListener('input',go);go();
})();
