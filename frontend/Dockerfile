FROM node:12
RUN mkdir /var/steward
COPY dist/ /var/steward/dist
COPY package.json /var/steward/package.json
COPY app_no_auth.js /var/steward/app_no_auth.js
COPY app.js /var/steward/app.js
WORKDIR /var/steward
RUN npm install express
RUN npm install path
RUN npm install -g serve 
RUN npm install axios
RUN npm install cookie-parser
CMD [ "node", "app_no_auth.js"]
