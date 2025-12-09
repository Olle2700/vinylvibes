const burger = document.querySelector(".burger");
const nav = document.querySelector("nav");

// ##############################
async function server(url, method, data_source_selector, function_after_fetch){
  let conn = null
  if( method.toUpperCase() == "POST" ){
    const data_source = document.querySelector(data_source_selector)
    conn = await fetch(url, {
      method: method,
      body: new FormData(data_source)
    })    
  }
  const data_from_server = await conn.text()
  if( ! conn){ console.log("error connecting to the server") }
  window[function_after_fetch](data_from_server)
}


// ##############################
function get_search_results(url, method, data_source_selector, function_after_fetch){
  const txt_search_for = document.querySelector("#txt_search_for")
  if( txt_search_for.value == ""  ){ 
    console.log("empty search"); 
    document.querySelector("#search_results").innerHTML = ""
    document.querySelector("#search_results").classList.add("d-none")
    return false 
  }
  server(url, method, data_source_selector, function_after_fetch)
}
// ##############################
function parse_search_results(data_from_server){
  // console.log(data_from_server)
  data_from_server = JSON.parse(data_from_server)
  let users = ""
  data_from_server.forEach( (user) => {
    let user_avatar_path = user.user_avatar_path ? user.user_avatar_path : "unknown.jpg"
    let html = `
        <div class="d-flex a-items-center">
            <img src="/static/images/${user_avatar_path}" class="w-8 h-8 rounded-full" alt="Profile Picture">
            <div class="w-full ml-2">
                <p class="">
                    ${user.user_first_name} ${user.user_last_name}
                    <span class="text-c-gray:+20 text-70">@${user.user_username}</span>
                </p>                
            </div>
            <button class="px-4 py-1 text-c-white bg-c-black rounded-lg">Follow</button>
        </div>`
    users += html
  })
  console.log(users)
  document.querySelector("#search_results").innerHTML = users
  document.querySelector("#search_results").classList.remove("d-none")
}




// ##############################
burger.addEventListener("click", () => {
  // toggle nav
  nav.classList.toggle("active");

  // toggle icon
  burger.classList.toggle("open");
});
