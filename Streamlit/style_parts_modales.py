# Define your CSS style for sidebar image (logo)
style_logo = """
    <style>
    .stMarkdown img {
        display: block;
        margin-left: auto;
        margin-right: auto;
        max-width: 60%;
        height: auto;
    }
    </style>
"""

footer = """
<style>
a:link,
a:visited {
  color: black;
  text-decoration: underline;
}

a:hover,
a:active {
  color: #dfab9a;
  text-decoration: underline;
}

.footer {
  position: fixed;
  left: 0;
  bottom: 0;
  width: 100%;
  background-color: white;
  color: black;
  text-align: center;
  z-index: 9999; /* Ensures it's on top of other elements */
}
</style>
<div class="footer">
<p><a href="http://situee.ch" >Située</a> pour Canton de Vaud – Canton de Genève – EPFL</p>
</div>
"""
